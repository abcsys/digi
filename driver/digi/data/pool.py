import os
import sys
import json
import threading
from abc import ABC, abstractmethod
from typing import List

import digi
from digi.data import logger, zjson
import zed


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
        self.client = zed.Client(
            base_url=os.environ.get("ZED_LAKE", "http://lake:6534")
        )

    def load(self, objects: List[dict], *,
             branch="main",
             encoding="zjson",
             same_type=False):
        # update event and processing time
        if encoding == "zjson":
            for o in objects:
                if "ts" in o and "event_ts" not in o:
                    o["event_ts"] = o["ts"]
                o["ts"] = digi.util.get_ts()
            data = "".join(zjson.encode(objects))
        else: # json
            for o in objects:
                if "ts" in o and "event_ts" not in o:
                    o["event_ts"] = o["ts"]
                o["ts"] = digi.util.get_ts(raw=False)
            data = "".join(json.dumps(o) for o in objects)
        self.lock.acquire()
        try:
            self.client.load(self.name, data, branch_name=branch)
        except Exception as e:
            digi.logger.warning(f"unable to load "
                                f"{data} to {self.name}: {e}")
        finally:
            self.lock.release()

    def query(self, query):
        return self.client.query(query)


def pool_name(g, v, r, n, ns):
    _, _, _ = g, v, r
    if ns == "default":
        return f"{n}"
    else:
        # TBD update digi creation
        return f"{ns}_{n}"


providers = {
    "zed": ZedPool
    # ...
}


def create_pool():
    global providers
    if digi.pool_provider == "":
        digi.pool_provider = "zed"

    if digi.pool_provider in {"none", "false"}:
        return None

    if digi.pool_provider not in providers:
        logger.fatal(f"unknown pool provider {digi.pool_provider}")
        sys.exit(1)

    return providers[digi.pool_provider](
        pool_name(*digi.duri)
    )
