import digi
import digi.data.sync as sync
import digi.data.util as util
from digi.data import logger


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
            dataflow, combine_dataflow = ig.get("dataflow", ""), \
                                         ig.get("dataflow_combine", "")
            for s in ig.get("source", []):
                sources += util.parse_source(s)
            for s in ig.get("sources", []):
                sources += util.parse_source(s)
            # TBD deduplicate sources
            if len(sources) == 0:
                continue

            _sync = sync.Sync(
                sources=sources,
                in_flow=dataflow,
                out_flow=combine_dataflow,
                dest=digi.pool.name,
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
                        f"with query: {_sync.query_str}")

    def update(self, config: dict):
        self._syncs = dict()

        names = list()
        for name, ig in config.items():
            dataflow = ig.get("dataflow", "")
            _sync = sync.Sync(
                sources=[digi.pool.name],
                in_flow=dataflow,
                out_flow="",
                dest=f"{digi.pool.name}@{name}",
            )
            self._syncs[name] = _sync
            names.append(name)
        util.create_branches_if_not_exist(digi.pool.name, names)

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
    if digi.on.new_mount(diff):
        digi.router.ingress.restart(config)


@digi.on.ingress
def do_ingress(config):
    digi.router.ingress.restart(config)


@digi.on.egress
def do_egress(config):
    digi.router.egress.restart(config)


def create_router():
    return Router()
