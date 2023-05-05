import digi
import digi.data.sync as sync
import digi.data.util as util
import digi.data.sourcer as sourcer
from digi.data import logger, zed, util
from digi.data import flow as flow_lib

"""
A router contains a collection of pipelets organized as ingresses and egresses.
Each pipelet is implemented as a digi.data.sync.Sync object that copies and ETL
data between a source data pool and a destination data pool. 
"""


class Router:
    def __init__(self):
        self.ingress = Ingress()
        self.egress = Egress()


class Ingress:
    def __init__(self):
        self._syncs = dict()

    def start(self):
        for name, _sync in self._syncs.items():
            _sync.start()
            logger.info(f"started ingress sync {name} "
                        f"with query: {_sync.query_str}")

    def stop(self):
        for _, _sync in self._syncs.items():
            _sync.stop()

    def update(self, config: dict):
        self._syncs = dict()

        for name, ig in config.items():
            if ig.get("pause", False):
                continue

            # resolve sources
            sources = list()
            source_quantifiers = set(ig.get("source", []) + ig.get("sources", []))
            use_sourcer = ig.get("use_sourcer", False)

            # concat and dedup sources
            for s in source_quantifiers:
                sources += sourcer.resolve(s, use_sourcer)

            logger.info(f"router: resolved {source_quantifiers} to {sources} "
                        f"for ingress {name}")
            if len(sources) == 0:
                continue

            # TBD add support for expressing ingress and egress type on the model
            # and the optional ingress-egress compatibility check in type.py

            # compile dataflow
            flow, flow_agg = ig.get("flow", ""), \
                             ig.get("flow_agg", "")
            if flow_agg == "":
                _out_flow = flow_lib.refresh_ts
            else:
                _out_flow = f"{flow_agg} | {flow_lib.refresh_ts}"

            # TBD add support for external pipelet
            # TBD disambiguate sync updates at fine-grained level
            # so that skip_history won't skip upon the config changes
            # or mount changes that don't affect this sync
            _sync = sync.Sync(
                sources=sources,
                in_flow=flow,
                out_flow=_out_flow,
                dest=digi.pool.name,
                eoio=ig.get("eoio", True),
                patch_source=ig.get("patch_source", False),
                client=zed.Client(),
                owner=digi.name,
                min_ts=util.now() if ig.get("skip_history", False) else util.min_time()
            )
            self._syncs[name] = _sync

    def restart(self, config: dict):
        self.stop()
        self.update(config=config)
        self.start()


class Egress:
    INIT = {"__meta": "init"}

    def __init__(self):
        self._syncs = dict()

    def start(self):
        for name, _sync in self._syncs.items():
            _sync.start()
            logger.info(f"started egress sync {name} "
                        f"with query:\n{_sync.query_str}")

    def stop(self):
        for _, _sync in self._syncs.items():
            _sync.stop()

    def update(self, config: dict):
        self._syncs = dict()

        for name, eg in config.items():
            if eg.get("driver_managed", False) \
                    or eg.get("pause", False):
                continue

            flow = eg.get("flow", "")
            out_flow = f"{flow_lib.drop_meta} | {flow_lib.refresh_ts}"
            if eg.get("de_id", False):
                out_flow += f"| {flow_lib.de_id}"
            if eg.get("link", False):
                out_flow += f"| {flow_lib.link}"

            # TBD support external sources including external lakes
            _sync = sync.Sync(
                sources=[digi.pool.name],
                in_flow=flow,
                out_flow=out_flow,
                dest=f"{digi.pool.name}@{name}",
                eoio=eg.get("eoio", True),
                client=zed.Client(),
                owner=digi.name,
            )
            self._syncs[name] = _sync
            # TBD garbage collect unused branches
            digi.pool.create_branch_if_not_exist(name)

    def restart(self, config: dict):
        self.stop()
        self.update(config=config)
        self.start()


@digi.on.mount
def do_mount(model, diff):
    config = model.get("ingress", {})
    # TBD move new_mount to decorator
    # TBD filter to relevant mounts only
    # XXX mount removal doesn't provide new data
    if digi.on.mount_change(diff):
        digi.router.ingress.restart(config)


@digi.on.ingress(prio=128)  # handler runs at last XXX sys.maxsize
def do_ingress(config):
    digi.router.ingress.restart(config)


@digi.on.egress(prio=128)
def do_egress(config):
    digi.router.egress.restart(config)


def create_router():
    return Router()
