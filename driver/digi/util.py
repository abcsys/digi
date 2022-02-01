import os
import uuid
import time
import asyncio
import contextlib
import threading
import datetime

import digi
import inflection
import logging
from typing import (
    Tuple, Callable, Union, Any, Iterable
)
from functools import reduce

import kubernetes
from kubernetes import config
from kubernetes.client.rest import ApiException

import kopf
from kopf._core.intents.registries import SmartOperatorRegistry as KopfRegistry

logger = logging.getLogger(__name__)
logger.setLevel(digi.log_level)

try:
    # use service config
    config.load_incluster_config()
except:
    # use kubeconfig
    config.load_kube_config()


class DriverError:
    GEN_OUTDATED = 41


_api = kubernetes.client.CustomObjectsApi()


def run_operator(registry: KopfRegistry,
                 log_level=logging.INFO,
                 skip_log_setup=False,
                 ) -> (threading.Event, threading.Event):
    clusterwide = os.environ.get("CLUSTERWIDE", True)
    kopf_logging = os.environ.get("KOPFLOG", "true") == "true"
    if not kopf_logging:
        kopf_logger = logging.getLogger("kopf")
        kopf_logger.propagate = False
        kopf_logger.handlers[:] = [logging.NullHandler()]

    ready_flag = threading.Event()
    stop_flag = threading.Event()

    def kopf_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with contextlib.closing(loop):
            if not skip_log_setup:
                # XXX (@kopf) disallow kopf configure root logger
                kopf.configure(verbose=log_level <= logging.DEBUG,
                               debug=log_level <= logging.DEBUG,
                               quiet=kopf_logging and log_level <= logging.INFO)
            loop.run_until_complete(kopf.operator(
                ready_flag=ready_flag,
                stop_flag=stop_flag,
                registry=registry,
                clusterwide=clusterwide,
            ))

    thread = threading.Thread(target=kopf_thread)
    thread.start()
    logger.info(f"started an operator")
    return ready_flag, stop_flag


class NamespacedName:
    def __init__(self, n, ns="default"):
        self.name = n
        self.namespace = ns


def uuid_str(length=4):
    return str(uuid.uuid4())[:length]


def spaced_name(n, ns) -> str:
    return f"{ns}/{n}"


def trim_default_space(n):
    return n.replace("default/", "")


def simple_name(n):
    return trim_default_space(n)


def trim_gv(gvr):
    return gvr.split("/")[-1]


def gvr_from_body(b):
    g, v = tuple(b["apiVersion"].split("/"))
    r = inflection.pluralize(b["kind"].lower())
    return g, v, r


def trim_attr(spec: dict, attrs: set) -> dict:
    # BFS
    to_visit = [spec]
    for n in to_visit:
        to_trim = list()
        if type(n) is not dict:
            continue
        for k, v in n.items():
            if k not in attrs:
                to_visit.append(v)
            else:
                to_trim.append(k)
        for k in to_trim:
            n.pop(k, {})
    return spec


def apply_diff(model: dict, diff: list) -> dict:
    for op, fs, old, new in diff:
        if len(fs) == 0:
            continue
        if op in {"add", "change"}:
            n = model
            for f in fs[:-1]:
                if f not in n:
                    n[f] = dict()
                n = n[f]
            n[fs[-1]] = new
    return model


def parse_spaced_name(nsn) -> Tuple[str, str]:
    parsed = nsn.split("/")
    if len(parsed) < 2:
        return parsed[0], "default"
    # name, namespace
    return parsed[1], parsed[0]


def parse_gvr(gvr: str, g="", v="") -> Tuple[str, ...]:
    parsed = tuple(gvr.lstrip("/").split("/"))
    assert len(parsed) == 3, f"{gvr} not in form of '[/]group/version/plural'"
    # if len(parsed) != 3:
    #     assert g != "" and v != "", "provide group and version to complete the gvr"
    #     return g, v, parsed[-1]
    return parsed


def model_id(g, v, r, n, ns) -> str:
    return f"{g}/{v}/{r}/{spaced_name(n, ns)}"


def gvr(g, v, r) -> str:
    return f"{g}/{v}/{r}"


def is_gvr(s: str) -> bool:
    return len(s.split("/")) == 3


def normalized_gvr(s, g, v) -> str:
    r = s.split("/")[-1]
    return f"{g}/{v}/{r}"


def normalized_nsn(s: str) -> str:
    if "/" not in s:
        return "default/" + s
    else:
        return s


def safe_attr(s):
    return s.replace(".", "-")


def parse_model_id(s) -> Tuple[str, str, str, str, str]:
    ps = s.lstrip("/").split("/")
    assert len(ps) in {4, 5}
    if len(ps) == 4:
        return ps[0], ps[1], ps[2], ps[3], "default"
    return ps[0], ps[1], ps[2], ps[4], ps[3]


def get_spec(g, v, r, n, ns) -> (dict, str, int):
    global _api

    try:
        o = _api.get_namespaced_custom_object(group=g,
                                              version=v,
                                              namespace=ns,
                                              name=n,
                                              plural=r,
                                              )
    except ApiException as e:
        logger.warning(f"unable to get model {n}:", e)
        return None
    return o.get("spec", {}), \
           o["metadata"]["resourceVersion"], \
           o["metadata"]["generation"]


def patch_spec(g, v, r, n, ns, spec: dict, rv=None):
    global _api
    try:
        resp = _api.patch_namespaced_custom_object(group=g,
                                                   version=v,
                                                   namespace=ns,
                                                   name=n,
                                                   plural=r,
                                                   body={
                                                       "metadata": {} if rv is None else {
                                                           "resourceVersion": rv,
                                                       },
                                                       "spec": spec,
                                                   },
                                                   )
        return resp, None
    except ApiException as e:
        return None, e


def check_gen_and_patch_spec(g, v, r, n, ns, spec, gen):
    # patch the spec atomically if the current gen is
    # less than the given spec
    while True:
        _, rv, cur_gen = get_spec(g, v, r, n, ns)
        if gen < cur_gen:
            e = ApiException()
            e.status = DriverError.GEN_OUTDATED
            e.reason = f"generation outdated {gen} < {cur_gen}"
            return cur_gen, None, e

        resp, e = patch_spec(g, v, r, n, ns, spec, rv=rv)
        if e is None:
            return cur_gen, resp, None
        if e.status == 409:
            logger.info(f"unable to patch {n} due to conflict; retry")
        else:
            logger.warning(f"patch error {e}")
            return cur_gen, resp, e


# utils
def put(path, src, target, transform=lambda x: x):
    if not isinstance(target, dict):
        return

    ps = path.split(".")
    for p in ps[:-1]:
        if p not in target:
            return
        target = target[p]

    if not isinstance(src, dict):
        if src is None:
            target[ps[-1]] = None
        else:
            target[ps[-1]] = transform(src)
        return

    for p in ps[:-1]:
        if p not in src:
            return
        src = src[p]
    target[ps[-1]] = transform(src[ps[-1]])


def deep_get(d: dict, path: Union[str, Iterable], default=None) -> Any:
    """accepts paths in form root.'digi.dev/test'.control.power"""
    if "'" in path or '"' in path:
        path = path.replace('"', "'")
        parsed = list()
        for i, seg in enumerate(path.split("'")):
            if seg == "":
                continue
            if i % 2 != 0:
                parsed.append(seg)
            else:
                parsed += seg.strip(".").split(".")
        path = parsed
    else:
        path = path.split(".") if isinstance(path, str) else path
    return reduce(lambda _d, key: _d.get(key, default)
    if isinstance(_d, dict) else default, path, d)


def deep_set(d: dict, path: Union[str, Iterable], val: Any, create=True):
    if not isinstance(d, dict):
        return
    if isinstance(path, str):
        keys = path.split(".")
    elif isinstance(d, Iterable):
        keys = path
    else:
        return
    for k in keys[:-1]:
        if k not in d:
            if create:
                d[k] = {}
            else:
                return
        d = d[k]
    d[keys[-1]] = val


def get_inst(d: dict, gvr_str) -> dict:
    inst = dict()
    for _n, body in d.get(gvr_str, {}).items():
        i = body.get("spec", None)
        if i is not None:
            inst[_n] = i
    return inst


def deep_set_all(ds, path: str, val):
    if isinstance(ds, list):
        for d in ds:
            deep_set(d, path, val)
    elif isinstance(ds, dict):
        for _, d in ds.items():
            deep_set(d, path, val)


def mount_size(mounts: dict, gvr_set: set = None,
               has_spec=False, cond: Callable = lambda x: True):
    count = 0
    for typ, models in mounts.items():
        if gvr_set is not None and typ not in gvr_set:
            continue

        for _, m in models.items():
            if not cond(m):
                continue
            if has_spec:
                count += 1 if "spec" in m else 0
            else:
                count += 1
    return count


def typ_attr_from_child_path(child_path):
    return child_path[2], child_path[-2]


def first_attr(attr, d: dict):
    if type(d) is not dict:
        return None
    if attr in d:
        return d[attr]
    for k, v in d.items():
        v = first_attr(attr, v)
        if v is not None:
            return v
    return None


def first_type(mounts):
    if type(mounts) is not dict or len(mounts) == 0:
        return None
    return list(mounts.keys())[0]


def full_gvr(a: str) -> str:
    # full gvr: group/version/plural
    if len(a.split("/")) == 1:
        return "/".join([os.environ["GROUP"],
                         os.environ["VERSION"],
                         a])
    else:
        return a


def gvr_equal(a: str, b: str) -> bool:
    return full_gvr(a) == full_gvr(b)


# TBD deprecate
class Auri:
    def __init__(self, **kwargs):
        self.group = str(kwargs["group"])
        self.version = str(kwargs["version"])
        self.kind = str(kwargs["kind"]).lower()
        self.resource = inflection.pluralize(self.kind)
        self.name = str(kwargs["name"])
        self.namespace = str(kwargs["namespace"])
        self.path = str(kwargs["path"])

    def gvr(self) -> tuple:
        return self.group, self.version, self.resource

    def gvk(self) -> tuple:
        return self.group, self.version, self.kind

    def auri(self):
        return self.group, self.version, self.resource, self.name, self.namespace

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"" \
               f"/{self.group}" \
               f"/{self.version}" \
               f"/{self.kind}" \
               f"/{self.namespace}" \
               f"/{self.name}{self.path}"


def parse_auri(s: str) -> Auri or None:
    ps = s.partition(".")
    main_segs = ps[0].lstrip("/").split("/")
    attr_path = "" if len(ps) < 2 else "." + ps[2]

    parsed = {
        2: lambda x: {
            "group": "digi.dev",
            "version": "v1",
            "kind": x[0],
            "name": x[1],
            "namespace": "default",
            "path": attr_path,
        },
        3: lambda x: {
            "group": "digi.dev",
            "version": "v1",
            "kind": x[0],
            "name": x[2],
            "namespace": x[1],
            "path": attr_path,
        },
        5: lambda x: {
            "group": x[0],
            "version": x[1],
            "kind": x[2],
            "name": x[3],
            "namespace": x[4],
            "path": attr_path,
        },
    }.get(len(main_segs), lambda: {})(main_segs)

    if parsed is None:
        return None
    return Auri(**parsed)


class Loader(threading.Thread):
    def __init__(self, load_fn: callable, load_interval: float = 1):
        threading.Thread.__init__(self)
        self.load_fn = load_fn
        self.load_interval = load_interval
        self._stop_flag = threading.Event()

    def run(self):
        self._stop_flag.clear()
        while not self._stop_flag.is_set():
            self.load_fn()
            time.sleep(self.load_interval)

    def stop(self):
        self._stop_flag.set()

    def reset(self, load_interval: float = None) -> None:
        if load_interval is not None:
            self.load_interval = load_interval
        self.stop()


def name_from_auri(auri: tuple):
    return auri[3]


update = deep_set
get = deep_get

def get_ts():
    return datetime.datetime.now().isoformat() + "Z"
