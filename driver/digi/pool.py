import sys
import json
import datetime
from abc import ABC, abstractmethod
from typing import List

import zed
import digi
from digi import logger

lake_url = "http://lake:6534"


class Pool(ABC):
    @abstractmethod
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def create(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def load(self, objects: List[dict]):
        raise NotImplementedError

    @abstractmethod
    def query(self, query: str):
        raise NotImplementedError


class ZedPool(Pool):
    def __init__(self, name):
        super().__init__(name)
        self.client = zed.Client(base_url=lake_url)

    def create(self):
        self.client.create_pool(self.name)

    def load(self, objects: List[dict]):
        ts = get_ts()
        for o in objects:
            # TBD if ts already exist, rename it to event_ts
            o["ts"] = ts
        data = "".join(json.dumps(o) for o in objects)
        self.client.load(self.name, data)

    def query(self, query):
        self.client.query(query)


def pool_name(g, v, r, n, ns):
    _, _, _ = g, v, r
    if ns == "default":
        return f"{n}"
    else:
        return f"{ns}-{n}"


def get_ts():
    return datetime.datetime.now().isoformat() + "Z"


providers = {
    "zed": ZedPool
    # ...
}


def new():
    global providers
    pool_provider = digi.pool_provider

    if pool_provider == "":
        pool_provider = "zed"

    if pool_provider in {"none", "false"}:
        return None

    elif pool_provider not in providers:
        logger.fatal(f"unknown pool provider {pool_provider}")
        sys.exit(1)
    else:
        return providers[pool_provider](
            pool_name(*digi.auri)
        )

pool = new()
