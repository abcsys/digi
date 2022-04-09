import os
import time
import datetime
import threading
import typing
import requests
import json
import yaml
from collections import defaultdict

from . import zed, zjson  # TBD use upstream

default_lake_url = os.environ.get("ZED_LAKE", "http://localhost:9867")


class Sync(threading.Thread):
    """Many-to-one sync between data pools on Zed lake."""
    SOURCE_COMMIT = 1
    SKIP = 2

    def __init__(self,
                 sources: typing.List[str],
                 dest: str,
                 in_flow: str = "",
                 out_flow: str = "",
                 *,
                 poll_interval: float = -1,  # sec, <0: use push
                 eoio: bool = True,  # exactly-once in-order
                 patch_source: bool = False,
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
        self.patch_source = patch_source
        # if eoio enabled, the sync agent will
        # process only those records that contain
        # a 'ts' field; XXX assume pool key is ts
        self.eoio = eoio
        self.client = zed.Client(base_url=lake_url) if client is None else client
        self.source_ts = self._fetch_source_ts()  # track {source: max(ts)}
        self.source_pool_ids = self._fetch_source_pool_ids()
        self.source_set = set(self.sources)
        self.query_str = self._make_query()

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
        records = self.read()
        if len(records) != 0:
            self.load(records)

    def read(self) -> list:
        records = list()
        if self.eoio:
            self.query_str = self._make_query()
        for r in self.client.query(self.query_str):
            if "__from" not in r:
                records.append(r)
                continue
            source, max_ts = r["__from"], r["max_ts"]
            if self.eoio:
                if max_ts is None:
                    raise Exception(f"no ts found in records from {source}")
                if source not in self.source_ts:
                    self.source_ts[source] = max_ts
                else:
                    self.source_ts[source] = max(max_ts, self.source_ts[source])
            else:
                self.source_ts[source] = datetime.datetime.min
        return records

    def load(self, records: list):
        records = "\n".join(zjson.encode(records))
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
        in_str = "from (\n"
        for source in self.sources:
            cur_ts = self.source_ts.get(source, datetime.datetime.min)
            filter_flow = f"ts > {zjson.encode_datetime(cur_ts)} |" \
                if self.eoio else ""
            patch_source_flow = f"put from := '{source}' |" \
                if self.patch_source else ""
            in_str += f"pool {source} => {filter_flow} {patch_source_flow} fork (" \
                      f"=> select max(ts) as max_ts | put __from := '{source}' " \
                      f"=> {'pass' if self.in_flow == '' else self.in_flow})"
            if len(self.sources) > 1:
                in_str += "\n"
        in_str += ")\n"  # wrap up from clause
        out_str = f"switch (case has(__from) => pass default => " \
                  f"{'pass' if self.out_flow == '' else self.out_flow})"
        return f"{in_str} | sort this | {out_str}"

    def _source_ts_json(self) -> str:
        return json.dumps({
            source: zjson.encode_datetime(ts)
            for source, ts in self.source_ts.items()
        })

    def _fetch_source_ts(self) -> dict:
        source_ts = dict()
        pool, branch = self._denormalize_one(self.dest)
        # filter to branches that have at least one commit
        branch_flow = f"from {pool}:branches | " \
                      f"select branch.name as branch," \
                      f"branch.commit as commit |" \
                      f"commit > 0x{'0' * 40}"
        if branch not in set(
                r["branch"] for r in self.client.query(branch_flow)
        ):
            return source_ts
        meta_flow = f"from {self.dest}:log | " \
                    f"typeof(this)==<Commit> | " \
                    f"over meta | " \
                    f"max(cast(value, <time>)) by key | " \
                    f"rename max_ts:=max"
        for r in self.client.query(meta_flow):
            source_ts[r["key"][0]] = r["max_ts"]
        return source_ts

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


class Watch(Sync):
    """A destination-less sync that runs a UDF in once()."""

    def __init__(self, fn: typing.Callable,
                 source_ts=None, *args, **kwargs):
        self.fn = fn
        self.source_ts = source_ts

        super().__init__(dest="none", *args, **kwargs)

    def once(self):
        self.fn(self.read())

    def _fetch_source_ts(self) -> dict:
        if self.source_ts is None:
            return defaultdict(lambda: datetime.datetime.min)
        else:
            return self.source_ts


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
