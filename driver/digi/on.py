import inspect
from collections import OrderedDict

import digi.util as util
import digi.filter as filter_
from digi.reconcile import rc

"""Filters."""


def meta(*args, **kwargs):
    # if decorator not parameterized
    if len(args) >= 1 and callable(args[0]):
        _attr(path="meta", *args, **kwargs)
        return args[0]

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="meta." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="meta." + kwargs.pop("path"), *args, **kwargs)
        return fn

    return decorator


def control(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        _attr(path="control", *args, **kwargs)
        return args[0]

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="control." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="control." + kwargs.pop("path"), *args, **kwargs)
        return fn

    return decorator


def data(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        _attr(path="data", *args, **kwargs)
        return args[0]

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="data." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="data." + kwargs.pop("path"), *args, **kwargs)
        return fn

    return decorator


def obs(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        _attr(path="obs", *args, **kwargs)
        return args[0]

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="obs." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="obs." + kwargs.pop("path"), *args, **kwargs)
        return fn

    return decorator


def mount(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        _attr(path="mount", *args, **kwargs)
        return args[0]

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="mount." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="mount." + kwargs.pop("path"), *args, **kwargs)
        return fn

    return decorator


# XXX test path
def attr(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        _attr(path=".", *args, **kwargs)
        return args[0]

    def decorator(fn):
        _attr(fn, *args, **kwargs)
        return fn

    return decorator

model = attr

def _attr(fn, path=".", prio=0):
    # preprocess the path str -> tuple of str
    _path = list()
    ps = path.split(".")

    child_typ = None

    if path == ".":
        _path = ["."]
    elif ps[0] == "mount":
        # XXX better . operator handling; use regex
        ps_gvr = path.split("/")
        assert len(ps_gvr) == 1 or len(ps_gvr) == 3
        if len(ps) == 1:
            # @mount w/o parameters
            _path = ps
        elif len(ps_gvr) == 1:
            # this gvr does not have group and version
            gvr = util.gvr(rc.g, rc.v, ps[1])
            ps[1], child_typ = gvr, gvr
            _path = ps
        elif len(ps_gvr) == 3:
            # TBD handle dot in version
            gvr = util.gvr(ps_gvr[0].replace("mount.", ""),
                           ps_gvr[1],
                           ps_gvr[2].split(".")[0])
            child_typ = gvr
            _path = ["mount", gvr] + ps_gvr[2].split(".")[1:]
    else:
        _path = ps
    # XXX assume default gv in gvr until fix dot in path literal;
    # _path = path.split(".")

    # TBD: join multiple path to allow multiple decorators per handler
    _path = tuple(_path)

    sig = inspect.signature(fn)

    # allow the handler declaration to omit arguments
    # the handler takes in argument in form of [subview, view, old_view]
    kwarg_filter = dict()
    args = OrderedDict(sig.parameters)

    # allow aliases
    for p in ["subview", "sub_view", "sv"]:
        if p in sig.parameters:
            kwarg_filter.update({"subview": p})
            args[p] = None

    for p in ["proc_view", "pv", "cur", "parent", "root", "model"]:
        if p in sig.parameters:
            kwarg_filter.update({"proc_view": p})
            args[p] = None

    for p in ["view", "v"]:
        if p in sig.parameters:
            kwarg_filter.update({"view": p})
            args[p] = None

    for p in ["old_view", "ov", "o"]:
        if p in sig.parameters:
            kwarg_filter.update({"old_view": p})
            args[p] = None

    for p in ["mount", "mounts", "mt", "mts",
              "child", "children"]:
        if p in sig.parameters:
            kwarg_filter.update({"mount": p})
            args[p] = None

    for p in ["obs"]:
        if p in sig.parameters:
            kwarg_filter.update({"obs": p})
            args[p] = None

    for p in ["back_prop", "bp"]:
        if p in sig.parameters:
            kwarg_filter.update({"back_prop": p})
            args[p] = None

    for p in ["diff"]:
        if p in sig.parameters:
            kwarg_filter.update({"diff": p})
            args[p] = None

    for p in ["typ", "child_typ"]:
        if p in sig.parameters:
            kwarg_filter.update({"typ": p})
            args[p] = None

    for i, (k, v) in enumerate(args.items()):
        if v is None:
            continue
        if i == 0:
            kwarg_filter["subview"] = k
        elif i == 1:
            kwarg_filter["proc_view"] = k
        elif i == 2:
            kwarg_filter["view"] = k
        elif i == 3:
            kwarg_filter["old_view"] = k
        elif i == 4:
            kwarg_filter["mount"] = k
        elif i == 5:
            kwarg_filter["obs"] = k
        elif i == 6:
            kwarg_filter["back_prop"] = k
        elif i == 7:
            kwarg_filter["diff"] = k
        else:
            break

    def wrapper_fn(subview, proc_view, view,
                   old_view, mount, obs, back_prop,
                   diff):
        kwargs = dict()
        for _k, _v in [("subview", subview),
                       ("proc_view", proc_view),
                       ("view", view),
                       ("old_view", old_view),
                       ("mount", mount),
                       ("obs", obs),
                       ("back_prop", back_prop),
                       ("diff", diff),
                       ("typ", child_typ),
                       ]:
            if _k in kwarg_filter:
                kwargs[kwarg_filter[_k]] = _v
        fn(**kwargs)

    rc.add(handler=wrapper_fn,
           priority=prio,
           condition=filter_.has_diff,
           path=_path)
