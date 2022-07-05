import digi
from digi import on, util, filter
import typing
import random

"""
dbox provides utilities for handling a scene hierarchy:
- set random seed using meta.seed
- set children's meta.managed
- filter ``managed'' for handler event filtering in children;
  e.g. @on.mount(cond=dbox.managed)
- event generation loop. Generation interval controlled by gen_interval,
  default to -1 which pauses the event generation; 
  e.g. @dbox.loop(managed=False)
dbox uses its own global random generator instance to separate from
other use cases of random module.
"""
random = random.Random()


def init_default():
    """This adds the following handlers:
    - Handler that updates random.seed based on meta.seed
    - Handler that configures all mounts to managed. """
    seeding()
    managing()


init = init_default


def seeding():
    global random
    cur_seed = 42
    random.seed(cur_seed)

    @on.meta
    def do_seed(meta):
        nonlocal cur_seed
        seed = meta.get("seed")
        if seed != cur_seed:
            cur_seed = seed
            if cur_seed is not None:
                random.seed(seed)


def managing():
    # TBD mount filter on new children (skip other updates)
    # TBD model class that contains advanced/processed events
    @on.mount
    def do_manage(mounts):
        manage(mounts)


def manage(mounts, skip_gvr=None):
    if skip_gvr is None:
        skip_gvr = {}
    for gvr, mocks in mounts.items():
        if gvr in skip_gvr:
            continue
        for _, mock in mocks.items():
            util.update(mock, "spec.meta.managed", True)


def managed(proc_spec, diff, *args, **kwargs):
    """handler filter decides when to skip reconciliation.
    Used as e.g. @on.mount(cond=dbox.managed)"""
    _, _ = args, kwargs
    managed = util.get(proc_spec, "meta.managed", False)
    if managed:
        return False
    else:
        return filter.path_changed(diff, ("meta", "managed")) or \
               filter.changed(proc_spec, diff, *args, **kwargs)


_loops = dict()


def loop(fn: typing.Callable, managed=True):
    """E.g. @dbox.loop(managed=False)"""
    global _loops
    _loops[fn.__name__] = util.Loop(loop_fn=fn)

    @on.meta
    def do_loop(meta):
        nonlocal managed
        i, _managed = meta.get("gen_interval", -1), \
                      managed and meta.get("managed", False)
        _loops[fn.__name__].stop()
        if i > 0 and not _managed:
            _loop = digi.util.Loop(
                loop_fn=fn,
                loop_interval=i,
            )
            _loops[fn.__name__] = _loop
            _loop.start()
