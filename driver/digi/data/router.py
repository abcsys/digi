import digi
import digi.data.sync as sync
import digi.data.util as util
from digi.data import logger


class Router:
    def __init__(self):
        self.ingress_sync = dict()
        self.egress_sync = dict()
        self.sources = dict()

    def start_ingress(self):
        for name, _sync in self.ingress_sync.items():
            _sync.start()
            logger.info(f"started ingress sync {name} "
                        f"with query: {_sync.query_str}")

    def update_ingress(self, config: dict):
        self.ingress_sync = dict()

        for name, ig in config.items():
            sources = list()
            dataflow, combine_dataflow = ig.get("dataflow", ""), \
                                         ig.get("dataflow_combine", "")
            digi.logger.info(f"DEBUG: ingress {ig.get('sources')}")
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
                dest=digi.name,
            )
            self.ingress_sync[name] = _sync

    def stop_ingress(self):
        for _, _sync in self.ingress_sync.items():
            _sync.stop()

    def restart_ingress(self, config: dict):
        self.stop_ingress()
        self.update_ingress(config=config)
        self.start_ingress()

    def start_egress(self):
        for name, _sync in self.egress_sync.items():
            _sync.start()
            logger.info(f"started egress sync {name} "
                        f"with query: {_sync.query_str}")

    def update_egress(self, config: dict):
        self.egress_sync = dict()

        names = list()
        for name, ig in config.items():
            dataflow = ig.get("dataflow", "")
            _sync = sync.Sync(
                sources=[digi.name],
                in_flow=dataflow,
                out_flow="",
                dest=f"{digi.name}@{name}",
            )
            self.egress_sync[name] = _sync
            names.append(name)
        util.create_branches_if_not_exist(digi.name, names)

    def stop_egress(self):
        for _, _sync in self.egress_sync.items():
            _sync.stop()

    def restart_egress(self, config: dict):
        self.stop_egress()
        self.update_egress(config=config)
        self.start_egress()


@digi.on.mount
def do_mount(model, diff):
    config = model.get("ingress", {})
    # TBD filter to relevant mounts only
    digi.logger.info(f"DEBUG: on mount {diff}")
    if digi.on.new_mount(diff):
        digi.logger.info(f"DEBUG: on mount diff")
        digi.router.restart_ingress(config)


@digi.on.ingress
def do_ingress(config):
    digi.router.restart_ingress(config)


@digi.on.egress
def do_egress(config):
    digi.router.restart_egress(config)


def create_router():
    return Router()
