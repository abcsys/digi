import json
import datetime
from abc import ABC, abstractmethod
from typing import List

import zed

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
