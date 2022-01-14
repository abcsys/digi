import sys
import json
import datetime
import threading
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
        self.lock = threading.Lock()

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

    def load(self, objects: List[dict]):
        ts = get_ts()
        for o in objects:
            # TBD if ts already exist, rename it to event_ts
            o["ts"] = ts
        data = "".join(json.dumps(o) for o in objects)

        self.lock.acquire()
        try:
            self.client.load(self.name, data)
        finally:
            self.lock.release()

    def query(self, query):
        return self.client.query(query)


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


def create_pool() -> Pool or None:
    global providers

    if digi.pool_provider == "":
        digi.pool_provider = "zed"

    if digi.pool_provider in {"none", "false"} or digi.pool_provider is None:
        return None

    elif digi.pool_provider not in providers:
        logger.fatal(f"unknown pool provider {digi.pool_provider}")
        sys.exit(1)
    else:
        return providers[digi.pool_provider](
            pool_name(*digi.auri)
        )


pool = None
