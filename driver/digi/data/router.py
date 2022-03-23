import digi
import digi.data.sync as sync
import digi.data.util as util
from digi.data import logger


class Router:
    def __init__(self):
        self.ingress_sync = dict()
        self.egress_sync = dict()

    def start_ingress(self):
        for name, _sync in self.ingress_sync.items():
            _sync.start()
            logger.info(f"started ingress sync {name} "
                        f"with query: {_sync.query_str}")

    def update_ingress(self, config):
        self.ingress_sync = dict()

        for name, ig in config.items():
            sources, parsed_sources = ig.get("source", []), list()
            dataflow, combine_dataflow = ig.get("dataflow", ""), \
                                         ig.get("combine_dataflow", "")
            for s in sources:
                parsed_sources += util.parse_source(s)
            if len(parsed_sources) == 0:
                continue

            _sync = sync.Sync(
                sources=parsed_sources,
                in_flow=dataflow,
                out_flow=combine_dataflow,
                dest=digi.name,
            )
            self.ingress_sync[name] = _sync

    def stop_ingress(self):
        for _, _sync in self.ingress_sync.items():
            _sync.stop()

    def start_egress(self):
        for name, _sync in self.egress_sync.items():
            _sync.start()
            logger.info(f"started egress sync {name} "
                        f"with query: {_sync.query_str}")

    def update_egress(self, config: dict):
        self.egress_sync = dict()

        for name, ig in config.items():
            dataflow = ig.get("dataflow", "")
            _sync = sync.Sync(
                sources=[digi.name],
                in_flow=dataflow,
                out_flow="",
                dest=f"{digi.name}_egress",
            )
            self.egress_sync[name] = _sync

    def stop_egress(self):
        for _, _sync in self.egress_sync.items():
            _sync.stop()


@digi.on.mount
def do_mount(model, diff):
    digi.logger.info(f"DEBUG: {diff}")


@digi.on.ingress
def do_ingress(config):
    digi.router.stop_ingress()
    digi.router.update_ingress(
        config=config
    )
    digi.router.start_ingress()


@digi.on.egress
def do_egress(config):
    digi.router.stop_egress()
    digi.router.update_egress(
        config=config,
    )
    digi.router.start_egress()


def create_router():
    return Router()
