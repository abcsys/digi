import digi
import digi.data.sync as sync
import digi.data.util as util
from digi.data import logger, zed
from digi.data import flow as flow_lib


class Router:
    def __init__(self):
        self.ingress = Ingress()
        self.egress = Egress()


class Ingress:
    def __init__(self):
        self._syncs = dict()
        self.sources = dict()

    def start(self):
        for name, _sync in self._syncs.items():
            _sync.start()
            logger.info(f"started ingress sync {name} "
                        f"with query: {_sync.query_str}")

    def update(self, config: dict):
        self._syncs = dict()

        for name, ig in config.items():
            sources = list()
            flow, flow_agg = ig.get("flow", ""), \
                             ig.get("flow_agg", "")
            for s in ig.get("source", []):
                sources += util.parse_source(s)
            for s in ig.get("sources", []):
                sources += util.parse_source(s)
            # TBD deduplicate sources
            if len(sources) == 0:
                continue

            if flow_agg == "":
                _out_flow = flow_lib.refresh_ts
            else:
                _out_flow = f"{flow_agg} | {flow_lib.refresh_ts}"
            _sync = sync.Sync(
                sources=sources,
                in_flow=flow,
                out_flow=_out_flow,
                dest=digi.pool.name,
                eoio=ig.get("eoio", True),
                client=zed.Client(),
                owner=digi.name,
            )
            self._syncs[name] = _sync

    def stop(self):
        for _, _sync in self._syncs.items():
            _sync.stop()

    def restart(self, config: dict):
        self.stop()
        self.update(config=config)
        self.start()


class Egress:
    def __init__(self):
        self._syncs = dict()

    def start(self):
        for name, _sync in self._syncs.items():
            _sync.start()
            logger.info(f"started egress sync {name} "
                        f"with query:\n{_sync.query_str}")

    def update(self, config: dict):
        self._syncs = dict()

        for name, ig in config.items():
            flow = ig.get("flow", "")
            _sync = sync.Sync(
                sources=[digi.pool.name],
                in_flow=flow,
                out_flow=flow_lib.refresh_ts,
                dest=f"{digi.pool.name}@{name}",
                eoio=ig.get("eoio", True),
                client=zed.Client(),
                owner=digi.name,
            )
            self._syncs[name] = _sync
            # TBD garbage collect unused branches
            digi.pool.create_branch_if_not_exist(name)

    def stop(self):
        for _, _sync in self._syncs.items():
            _sync.stop()

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


@digi.on.ingress
def do_ingress(config):
    digi.router.ingress.restart(config)


@digi.on.egress
def do_egress(config):
    digi.router.egress.restart(config)


def create_router():
    return Router()
