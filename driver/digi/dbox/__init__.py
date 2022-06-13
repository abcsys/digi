import digi
from digi import on, util
import typing


# handler filter: if managed skip the handler during reconciliation
def managed(proc_spec, diff, *args, **kwargs):
    _, _ = args, kwargs
    managed = digi.util.get(proc_spec, "meta.managed", False)
    if managed:
        return False
    else:
        return digi.filter.path_changed(diff, ("meta", "managed")) or \
               digi.filter.changed(proc_spec, diff, *args, **kwargs)


loops = dict()


def loop(fn: typing.Callable):
    global loops
    loops[fn.__name__] = util.Loop(loop_fn=fn)

    @on.meta
    def do_meta(meta):
        i, managed = meta.get("gen_interval", -1), \
                     meta.get("managed", False)
        loops[fn.__name__].stop()
        if i > 0 and not managed:
            _loop = digi.util.Loop(
                loop_fn=fn,
                loop_interval=i,
            )
            loops[fn.__name__] = _loop
            _loop.start()
