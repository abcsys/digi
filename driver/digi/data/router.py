import digi
import digi.data.sync as sync
import digi.data.util as util
from digi.data import logger, zed
from digi.data import flow as flow_lib

import requests

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
            
    #TODO:
    #Router: move registry to a config file with an env var for its location
    
    def resolve_source(self, source_quantifier):
        try:
            sourcer_response = requests.get("http://sourcer:7534/resolve", 
                                            json={"source_quantifier" : source_quantifier}, 
                                            headers={"Content-Type": "application/json"})
            sourcer_response_json = sourcer_response.json() #dict containing {source_lake_url, sources, success}
            
            if sourcer_response_json["success"]:
                digi.logger.info(f"Used sourcer for source {source_quantifier}")
                return sourcer_response_json["sources"]
        except:
            pass
        
        digi.logger.info(f"Used parse_source for source {source_quantifier}")
        return util.parse_source(source_quantifier)

    def update(self, config: dict):
        self._syncs = dict()
        
        for name, ig in config.items():
            if ig.get("pause", False):
                continue

            sources = list()
            flow, flow_agg = ig.get("flow", ""), \
                             ig.get("flow_agg", "")
            use_sourcer = ig.get("use_sourcer", False)
            
            for s in set(ig.get("source", []) + ig.get("sources", [])):
                if use_sourcer:
                    sources += self.resolve_source(s)
                else:
                    sources += util.parse_source(s)

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
                patch_source=ig.get("patch_source", False),
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

    @staticmethod
    def _any_source():
        # TBD fetch all sources - digi and egresses
        # for digis that are mounted
        raise NotImplementedError


class Egress:
    INIT = {"__meta": "init"}

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
            if ig.get("driver_managed", False) \
                    or ig.get("pause", False):
                continue

            flow = ig.get("flow", "")
            _sync = sync.Sync(
                sources=[digi.pool.name],
                in_flow=flow,
                out_flow=f"{flow_lib.drop_meta} | {flow_lib.refresh_ts}",
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


@digi.on.ingress(prio=128)  # handler runs at last XXX sys.maxsize
def do_ingress(config):
    digi.router.ingress.restart(config)


@digi.on.egress(prio=128)
def do_egress(config):
    digi.router.egress.restart(config)


def create_router():
    return Router()
