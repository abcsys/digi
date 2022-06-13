import digi
from digi import on, util, filter
import typing


def managed(proc_spec, diff, *args, **kwargs):
    """handler filter decides when to skip reconciliation"""
    _, _ = args, kwargs
    managed = util.get(proc_spec, "meta.managed", False)
    if managed:
        return False
    else:
        return filter.path_changed(diff, ("meta", "managed")) or \
               filter.changed(proc_spec, diff, *args, **kwargs)


def manage(mounts, skip_gvr=None):
    if skip_gvr is None:
        skip_gvr = {}
    for gvr, mocks in mounts.items():
        if gvr in skip_gvr:
            continue
        for _, mock in mocks.items():
            util.update(mock, "spec.meta.managed", True)


_loops = dict()


def loop(fn: typing.Callable):
    global _loops
    _loops[fn.__name__] = util.Loop(loop_fn=fn)

    @on.meta
    def do_meta(meta):
        i, managed = meta.get("gen_interval", -1), \
                     meta.get("managed", False)
        _loops[fn.__name__].stop()
        if i > 0 and not managed:
            _loop = digi.util.Loop(
                loop_fn=fn,
                loop_interval=i,
            )
            _loops[fn.__name__] = _loop
            _loop.start()
