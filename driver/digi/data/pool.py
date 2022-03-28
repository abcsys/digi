import sys
import json
import threading
import datetime
from abc import ABC, abstractmethod
from typing import List

import digi
from digi.data import logger, zjson
from digi.data import zed


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

    @abstractmethod
    def create_branch_if_not_exist(self, query: str):
        raise NotImplementedError


class ZedPool(Pool):
    def __init__(self, name):
        super().__init__(name)
        self.client = zed.Client(
            base_url=digi.data.lake_url
        )

    def load(self, objects: List[dict], *,
             branch="main",
             encoding="zjson",
             same_type=False):
        # update event and processing time
        now = datetime.datetime.now()
        if encoding == "zjson":
            for o in objects:
                # event_ts will be attached at the first
                # data router if does exist from the source
                if "event_ts" not in o:
                    o["event_ts"] = o.get("ts", now)
                o["ts"] = now
            data = "".join(zjson.encode(objects))
        elif encoding == "json":
            now = zjson.encode_datetime(now)  # as str
            for o in objects:
                if "event_ts" not in o:
                    o["event_ts"] = o.get("ts", now)
                o["ts"] = now
            data = "\n".join(json.dumps(o) for o in objects)
        else:
            raise NotImplementedError

        self.lock.acquire()
        try:
            self.client.load(self.name, data,
                             branch_name=branch,
                             commit_author=digi.name,
                             meta="")
            # TBD load from digi also commits source ts in meta
        except Exception as e:
            digi.logger.warning(f"unable to load "
                                f"{data} to {self.name}: {e}")
        finally:
            self.lock.release()

    def query(self, query):
        return self.client.query(query)

    def create_branch_if_not_exist(self, branch: str):
        if not self.client.branch_exist(self.name, branch):
            self.client.create_branch(self.name, branch)


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
