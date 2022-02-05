import copy
import typing
import traceback
from collections import OrderedDict

import digi
import digi.util as util
import digi.filter as filter_
import digi.processor as processor


class HandlerType:
    BUILTIN = 1
    REFLEX = 2


class __Reconciler:
    def __init__(self):
        # handlers are stored as tuples (fn, condition, path, priority)
        # the higher the priority value, the higher the priority;
        # default priority is 0; low priority handlers are run first;
        # priority lower than 0 is skipped.
        # - condition: a function that decides whether the handler
        #   should be run or not.
        # - path: the attribute subtree the handler subscribes to

        # sorted list of handlers in execution order
        self.handlers = list()
        self.g = digi.g
        self.v = digi.v
        self.r = digi.r
        self.n = digi.n
        self.ns = digi.ns
        self.auri = digi.auri

        self._logger = digi.logger

        self.skip_gen = -1
        self.count = 0
        self.last_seen_gen = -1

        # handler info (e.g., priority) are used to
        # generate the self.handlers upon handler updates;
        # each of form (fn, condition, view_path, priority, type)
        # keyed by handler's name (fn.__name__)
        self._handler_info = OrderedDict()
        self._handler_info_updated = True
        # if a handler's update didn't get applied to the model
        # the handler is marked as pending and will be invoked
        # in future reconciliation to be executed again. The
        # handler object's id is used as the key.
        self._pending_handler = set()

        # most recent view of the model, served as an in-memory
        # read-only copy to be used in external application
        self._view = dict()

    def run(self, spec, old, diff, *args, **kwargs):
        spec = dict(spec)
        proc_spec = dict(spec)

        self._view = spec
        self._update_handler_info(spec, diff)
        self._compile_handler()

        for fn, cond, path, _ in self.handlers:
            if cond(proc_spec, diff, path, *args, **kwargs) \
                    or id(fn) in self._pending_handler:
                # handler edits the spec object
                try:
                    # TBD allow subview to be a forest
                    fn(
                        subview=safe_lookup(proc_spec, path),
                        proc_view=proc_spec,
                        view=spec, old_view=old,
                        mount=proc_spec.get("mount", {}),
                        obs=proc_spec.get("obs", {}),
                        back_prop=get_back_prop(diff),
                        diff=diff,
                    )
                    self._pending_handler.add(id(fn))
                except Exception as e:
                    self._logger.error(f"reconcile error: {e}")
                    self._logger.error(traceback.format_exc())
                    # TBD: expose driver status on model, e.g., obs.reason/or some debug attribute
                    return proc_spec
        return proc_spec

    def add(self, handler: typing.Callable,
            condition: typing.Callable,
            priority: int,
            path: tuple = (),
            typ=HandlerType.BUILTIN):

        n = handler.__name__

        if n in self._handler_info:
            # TBD perhaps use deterministic name
            n = n + util.uuid_str()

        self._handler_info[n] = {
            "fn": handler,
            "condition": condition,
            "view_path": path,
            "priority": priority,
            "type": typ,
        }

    def _update_handler_info(self, spec, diff):
        # check whether there is a reflex change
        _changed = not all(len(_path) < 2 or _path[1] != "reflex"
                           for _, _path, _, _ in diff)

        if _changed:
            reflexes = util.deep_get(spec, "reflex", {})

            # trim reflexes
            to_remove = list()
            for n, info in self._handler_info.items():
                if info["type"] == HandlerType.BUILTIN:
                    continue
                if n not in reflexes:
                    to_remove.append(n)

            for n in to_remove:
                self._handler_info.pop(n, {})

            # update handlers
            for n, r in reflexes.items():
                info = self._handler_info.get(n, {
                    "fn": do_nothing,
                    "condition": filter_.always,  # TBD conditioned reflex
                    "view_path": ".",
                    "priority": 0,
                    "type": HandlerType.REFLEX,
                })

                patch = dict()
                if "policy" in r:
                    patch.update({
                        "fn": self._new_reflex(r["policy"],
                                               r.get("processor", "py"))
                    })

                if "priority" in r:
                    patch.update({
                        "priority": r["priority"]
                    })

                info.update(patch)
                self._handler_info[n] = info

            self._handler_info_updated = True

    @staticmethod
    def _new_reflex(logic, proc="py"):
        if logic is None:
            return do_nothing
        if proc == "py":
            return processor.py(logic)
        if proc == "jq":
            return processor.jq(logic)
        ...

    def _compile_handler(self):
        if not self._handler_info_updated:
            return

        self.handlers = list()
        for _, hi in self._handler_info.items():
            # treat negative priority as disabled
            if hi["priority"] < 0:
                continue
            self.handlers.append((hi["fn"], hi["condition"],
                                  hi["view_path"], hi["priority"]))

        # sort by priority
        self.handlers = sorted(self.handlers, key=lambda x: x[3])
        self._handler_info_updated = False

    def view(self):
        return copy.deepcopy(self._view)

    def clear_pending(self):
        self._pending_handler.clear()


def safe_lookup(d: dict, path: tuple):
    if path == (".",):
        return d

    for k in path:
        d = d.get(k, {})
    return d


def do_nothing(*args, **kwargs):
    _, _ = args, kwargs


def get_back_prop(diff):
    bp = list()
    for op, path, old, new in diff:
        if op != "change" and op != "add":
            continue
        if len(path) < 3 or path[0] != "spec" \
                or path[1] != "mount":
            continue

        fs = set(path)
        if "intent" not in fs and "input" not in fs:
            continue
        bp.append((op, path, old, new))
    return bp


rc = __Reconciler()
