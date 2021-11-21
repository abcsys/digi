import json
import datetime
from abc import ABC, abstractmethod

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
    def load(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    def query(self, query: str):
        raise NotImplementedError

    @abstractmethod
    def _augment(self, data: dict, ts: bool = True) -> dict:
        raise NotImplementedError


class ZedPool(Pool):
    def __init__(self, name):
        super().__init__(name)
        self.client = zed.Client(base_url=lake_url)

    def create(self):
        self.client.create_pool(self.name)

    def load(self, data):
        data = self._augment(data)
        self.client.load(self.name, json.dumps(data))

    def query(self, query):
        self.client.query(query)

    def _augment(self, data, ts=True):
        data["ts"] = get_ts()
        return data


def pool_name(g, v, r, n, ns):
    _, _, _ = g, v, r
    if ns == "default":
        return f"{n}"
    else:
        return f"{ns}-{n}"

def get_ts():
    return datetime.datetime.now().isoformat() + "Z"
