import os
import digi
import digi.data.sync as sync
import digi.data.util as util
import digi.data.sourcer as sourcer
from digi.data import logger, zed, util
from digi.data import flow as flow_lib

import yaml
from kubernetes.client.rest import ApiException
from kubernetes import config, client

config.load_incluster_config()


"""
A router contains a collection of pipelets organized as ingresses and egresses.
Each pipelet is implemented as a digi.data.sync.Sync object that copies and ETL
data between a source data pool and a destination data pool.
"""


def create_custom_api_object(name, src, dst, in_flow, out_flow, interval, eoio, action="create"):
    '''
    Create a custom api object on k8s cluster

    :param name: name of the pipelet
    :param src: source data pool
    :param dst: destination data pool
    :param flow: flow expression
    :param interval: interval in seconds
    :param eoio: end of interval offset in seconds
    :param action: create or delete
    '''
    with client.ApiClient() as api_client:
        # Create an instance of the API class
        api_instance = client.CustomObjectsApi(api_client)

        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, "pipelet.yaml")) as f:
            body = yaml.load(f, Loader=yaml.FullLoader)

        body['metadata']['name'] = name

        intent = body['spec']['control']['intent']
        intent['src'] = src
        intent['dst'] = dst
        intent['flow'] = in_flow
        intent['interval'] = interval
        intent['eoio'] = eoio
        intent['action'] = action

        try:
            _ = api_instance.create_namespaced_custom_object(
                "knactor.io", "v1", digi.ns, "pipelets", body)
        except ApiException as e:
            logger.error(
                "Exception when calling CustomObjectsApi->create_cluster_custom_object: %s\n" % e)


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
            source_quantifiers = set(
                ig.get("source", []) + ig.get("sources", []))
            use_sourcer = ig.get("use_sourcer", False)
            pipelet_offload = ig.get("offload", False)

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
            # TBD cleanup created pipelets

            if pipelet_offload:
                # TBD add support for skip_history
                create_custom_api_object(
                    name=f"{digi.n}-ingress-{name}".replace("_", "-"),
                    src=sources,
                    dst=[digi.pool.name],
                    in_flow=flow,
                    out_flow=_out_flow,
                    interval=-1,
                    eoio=ig.get("eoio", True),
                    action="create"
                )
            else:
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
            digi.pool.create_branch_if_not_exist(name)
            # TBD garbage collect unused branches

            if eg.get("driver_managed", False) \
                    or eg.get("pause", False):
                continue

            flow = eg.get("flow", "")
            pipelet_offload = eg.get("offload", False)

            out_flow = f"{flow_lib.drop_meta} | {flow_lib.refresh_ts}"
            if eg.get("de_id", False):
                out_flow += f"| {flow_lib.de_id}"
            if eg.get("link", False):
                id = f"{digi.name}/{name}"
                out_flow += f"| {flow_lib.link(id)}"

            if pipelet_offload:
                # TBD cleanup created pipelets
                create_custom_api_object(
                    name=f"{digi.n}-egress-{name}".replace("_", "-"),
                    src=[digi.pool.name],
                    dst=[f"{digi.pool.name}@{name}"],
                    in_flow=flow,
                    out_flow=f"{flow_lib.drop_meta} | {flow_lib.refresh_ts}",
                    interval=-1,
                    eoio=eg.get("eoio", True),
                    action="create"
                )
            else:
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
