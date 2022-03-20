import os
import time
import threading
import json
import yaml

import zed

default_lake_url = os.environ.get("ZED_LAKE", "http://localhost:9867")


class Sync(threading.Thread):
    """Many-to-one sync between data pools on Zed lake."""

    def __init__(self,
                 sources: list,
                 dest: str,
                 in_flow: str = "",
                 out_flow: str = "",
                 *,
                 sync_interval: float = 1.0,  # sec
                 lake_url: str = default_lake_url,
                 ):
        assert len(sources) > 0 and dest != ""

        self.sources = sources
        self.dest = dest
        self.in_flow = in_flow
        self.out_flow = out_flow
        self.query_str = self._make_query()

        self.sync_interval = sync_interval
        self.client = zed.Client(base_url=lake_url)

        threading.Thread.__init__(self)
        self._stop_flag = threading.Event()

    def run(self):
        self._stop_flag.clear()
        while not self._stop_flag.is_set():
            self.once()
            time.sleep(self.sync_interval)

    def stop(self):
        self._stop_flag.set()

    def once(self):
        records = self.client.query(self.query_str)
        records = "".join(json.dumps(r) for r in records)
        self.client.load(self.dest, records)

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


def from_config(path: str) -> Sync:
    with open(path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return Sync(
        sources=config["sources"],
        dest=config["dest"],
        in_flow=config["in_flow"],
        out_flow=config["out_flow"],
    )


if __name__ == '__main__':
    from_config("demo.yaml").start()
