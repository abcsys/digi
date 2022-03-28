import os
import time
import threading

import digi
import requests
import typing
import yaml
import json
from . import zed, zjson  # TBD use upstream

default_lake_url = os.environ.get("ZED_LAKE", "http://localhost:9867")


class Sync(threading.Thread):
    """Many-to-one sync between data pools on Zed lake."""
    SOURCE_COMMIT = 1
    SKIP = 2

    def __init__(self,
                 sources: list,
                 dest: str,
                 in_flow: str = "",
                 out_flow: str = "",
                 *,
                 poll_interval: float = -1,  # sec, <0: use push
                 eoio: bool = True,  # exactly-once in-order
                 owner: str = "sync",  # commit author
                 lake_url: str = default_lake_url,
                 client: zed.Client = None,
                 ):
        assert len(sources) > 0 and dest != ""

        self.sources = self._normalize(sources)
        self.dest = self._normalize_one(dest)
        self.in_flow = in_flow  # TBD multi-in_flow
        self.out_flow = out_flow
        self.poll_interval = poll_interval
        self.owner = owner
        self.query_str = self._make_query()
        self.client = zed.Client(base_url=lake_url) if client is None else client
        self.source_pool_ids = self._fetch_source_pool_ids()
        self.source_set = set(self.sources)
        # when eoio is enabled, the sync agent will
        # process only those records that contain
        # a 'ts' field
        self.eoio = eoio
        # track {source: max(ts)}
        self.source_ts = dict()
        # TBD load source_ts from dest pool on restart

        threading.Thread.__init__(self)
        self._stop_flag = threading.Event()

    def run(self):
        self._stop_flag.clear()

        self.once()
        if self.poll_interval > 0:
            self._poll_loop()
        else:
            self._event_loop()

    def stop(self):
        self._stop_flag.set()

    def once(self):
        if self.eoio:
            records = list()
            self.query_str = self._make_query()
            for r in self.client.query(self.query_str):
                if "__from" not in r:
                    records.append(r)
                    continue
                source, max_ts = r["__from"], r["max_ts"]
                if max_ts is None:
                    raise Exception(f"no ts found in records from {source}")
                if source not in self.source_ts:
                    self.source_ts[source] = max_ts
                else:
                    self.source_ts[source] = max(max_ts, self.source_ts[source])
            records = "\n".join(zjson.encode(records))
        else:  # skip decode/encode
            raw = self.client.query_raw(self.query_str)
            records = "".join(json.dumps(r) for r in raw
                              if isinstance(r["type"], dict))
        if len(records) > 0:
            dest_pool, dest_branch = self._denormalize_one(self.dest)
            self.client.load(
                dest_pool, records,
                branch_name=dest_branch,
                commit_author=self.owner,
                meta=self._source_ts_json(),
            )

    def _event_loop(self):
        s = requests.Session()
        with s.get(f"{default_lake_url}/events",
                   headers=None, stream=True) as resp:
            lines = resp.iter_lines()
            for line in lines:
                if self._stop_flag.is_set():
                    return
                event = self._parse_event(line, lines)
                if event == Sync.SOURCE_COMMIT:
                    self.once()
                elif event == Sync.SKIP:
                    continue
                else:
                    raise NotImplementedError

    def _poll_loop(self):
        while not self._stop_flag.is_set():
            self.once()
            time.sleep(self.poll_interval)

    def _make_query(self) -> str:
        out_str = f"fork (=> has(__from) => " \
                  f"{'pass' if self.out_flow == '' else self.out_flow})"
        in_str = "from (\n"
        for source in self.sources:
            # TBD: use self.source_ts
            in_str += f"pool {source} => fork (" \
                      f"=> select max(ts) as max_ts | put __from := '{source}' " \
                      f"=> {'pass' if self.in_flow == '' else self.in_flow})"
            if len(self.sources) > 1:
                in_str += "\n"
        in_str += ")\n"  # wrap up from clause
        return f"{in_str} | yield this | {out_str}"

    def _source_ts_json(self) -> str:
        return json.dumps({
            source: zjson.encode_datetime(ts)
            for source, ts in self.source_ts.items()
        })

    def _fetch_source_ts(self):
        # TBD restore source_ts from commit meta
        raise NotImplementedError

    def _fetch_source_pool_ids(self) -> dict:
        return {
            f"0x{r['id'].hex()}": r["name"]
            for r in self.client.query("from :pools")
            if r["name"] in set(s.split("@")[0] for s in self.sources)
        }

    def _parse_event(self, line: bytes, lines: typing.Iterator) -> int:
        def substr(s, start, end):
            return (s.split(start))[1].split(end)[0]

        line = line.decode()
        if line == "event: branch-commit":
            data = next(lines).decode().lstrip("data: ")
            pool_id = substr(data, "pool_id:", ",")
            branch = substr(data, "branch:", ",").strip('"')
            # TBD cache commit_id
            # commit_id = substr(data, "commit_id:", ",")
            if pool_id in self.source_pool_ids:
                pool_name = self.source_pool_ids[pool_id]
                if f"{pool_name}@{branch}" in self.source_set:
                    return Sync.SOURCE_COMMIT
        return Sync.SKIP

    @staticmethod
    def _normalize(names: list) -> list:
        return [Sync._normalize_one(n) for n in names]

    @staticmethod
    def _normalize_one(name: str) -> str:
        """Return source in form of pool@main."""
        return f"{name}@main" if "@" not in name else name

    @staticmethod
    def _denormalize_one(name: str) -> tuple:
        pool, branch = name.split("@")
        return pool, branch


def from_config(path: str) -> Sync:
    with open(path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return Sync(
        sources=config["sources"],
        dest=config["dest"],
        in_flow=config.get("in_flow", ""),
        out_flow=config.get("out_flow", ""),
        poll_interval=config.get("poll_interval", -1),
    )


if __name__ == '__main__':
    from_config("demo.yaml").start()
