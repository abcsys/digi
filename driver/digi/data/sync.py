import os
import time
import threading

import requests
import typing
import json
import yaml
import zed

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
                 lake_url: str = default_lake_url,
                 ):
        assert len(sources) > 0 and dest != ""

        self.sources = self._normalize(sources)
        self.dest = self._normalize_one(dest)
        self.in_flow = in_flow  # TBD allow multi-in_flow
        self.out_flow = out_flow
        self.query_str = self._make_query()
        self.poll_interval = poll_interval
        self.client = zed.Client(base_url=lake_url)
        self.source_pool_ids = self._get_source_pool_ids()
        self.source_set = set(self.sources)

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
        records = self.client.query_raw(self.query_str)  # over zjson
        records = "".join(json.dumps(r) for r in records if isinstance(r["type"], dict))
        if len(records) > 0:
            dest_pool, dest_branch = self._denormalize_one(self.dest)
            self.client.load(dest_pool, records,
                             branch_name=dest_branch)

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
        in_str, out_str = "", self.out_flow
        if len(self.sources) > 1:
            in_str = "from (\n"
            for source in self.sources:
                in_str += f"pool {source}"
                if self.in_flow != "":
                    in_str += f" => {self.in_flow}"
                in_str += "\n"
            in_str += ")"
        else:
            in_str = f"from {self.sources[0]}"
            if self.in_flow != "":
                in_str += f" | {self.in_flow}"

        if out_str != "":
            return f"{in_str} | {out_str}"
        else:
            return in_str

    def _get_source_pool_ids(self):
        return {
            f"0x{r['id'].hex()}": r["name"]
            for r in self.client.query("from :pools")
            if r["name"] in set(s.split("@")[0] for s in self.sources)
        }

    def _parse_event(self, line: bytes, lines: typing.Iterator):
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

    def _normalize(self, names: list) -> list:
        return [self._normalize_one(n) for n in names]

    def _normalize_one(self, name: str) -> str:
        """Return source in form of pool@main."""
        return f"{name}@main" if "@" not in name else name

    def _denormalize_one(self, name: str) -> tuple:
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
