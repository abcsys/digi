import os
import sys
import logging
from collections import defaultdict
import kopf

import digi.util as util
from digi.util import parse_gvr, spaced_name, parse_spaced_name

"""
An embedded meta-actor that implements the mount semantics.

Event watch:
- Watch the parent model and identify the child models;
- Watch the child models;

Event propagation:
- On child's updates (intent and status): propagate to the child's 
  copy in the parent;
- On parent's updates (intent) on the child's copy: propagate to 
  the child's intent;
"""

if os.environ.get("STRICT_MOUNT", "true") == "true":
    TRIM_FROM_PARENT = {"status", "output", "obs", "meta"}
    TRIM_FROM_CHILD  = {"intent", "input"}
else:
    TRIM_FROM_PARENT = TRIM_FROM_CHILD = set()

class Watch:
    def __init__(self, g, v, r, n, ns="default", *,
                 create_fn=None,
                 resume_fn=None,
                 update_fn=None,
                 # TBD enable finalizer but avoid looping with multiple children
                 delete_fn=None, delete_optional=True,
                 field_fn=None, field="",
                 log_level=logging.INFO):
        self._registry = util.KopfRegistry()
        self._log_level = log_level
        _args = (g, v, r)
        _kwargs = {
            "registry": self._registry,
            # watch a specific model only
            "when": lambda name, namespace, **_: name == n and namespace == ns,
        }

        @kopf.on.startup(registry=self._registry)
        def configure(settings: kopf.OperatorSettings, **_):
            settings.persistence.progress_storage = kopf.AnnotationsProgressStorage()
            settings.posting.level = log_level

        if create_fn is not None:
            kopf.on.create(*_args, **_kwargs)(create_fn)
        if resume_fn is not None:
            kopf.on.resume(*_args, **_kwargs)(resume_fn)
        if update_fn is not None:
            kopf.on.update(*_args, **_kwargs)(update_fn)
        if delete_fn is not None:
            kopf.on.delete(*_args, **_kwargs, optional=delete_optional)(delete_fn)
        if field_fn is not None and field != "":
            kopf.on.field(field=field, *_args, **_kwargs)(field_fn)
        assert create_fn or resume_fn or update_fn or delete_fn, "no handler provided"

        self._ready_flag, self._stop_flag = None, None

    def start(self):
        self._ready_flag, self._stop_flag = util.run_operator(
            self._registry, log_level=self._log_level,
            skip_log_setup=True,
        )
        return self

    def stop(self):
        assert self._stop_flag, "watch has not started"
        self._stop_flag.set()
        return self


class Mounter:
    """Implements the mount semantics for a given (parent) digivice"""

    def __init__(self, g, v, r, n, ns="default",
                 log_level=logging.INFO):

        """ children event handlers """

        def on_child_create(body, meta, name, *args, **kwargs):
            _g, _v, _r = util.gvr_from_body(body)
            self._logger.info(f"on create child {name} gen {meta['generation']}")
            _sync_from_parent(_g, _v, _r, meta=meta, name=name,
                              attrs_to_trim=TRIM_FROM_PARENT,
                              *args, **kwargs)
            _sync_to_parent(_g, _v, _r, meta=meta, name=name,
                            attrs_to_trim=TRIM_FROM_CHILD,
                            *args, **kwargs)

        def on_child_update(body, meta, name, namespace,
                            *args, **kwargs):
            _g, _v, _r = util.gvr_from_body(body)
            _id = util.model_id(_g, _v, _r, name, namespace)

            self._logger.info(f"on child {name} gen {meta['generation']}")
            if meta["generation"] == self._children_skip_gen.get(_id, -1):
                self._logger.info(f"skipped child {name} gen {meta['generation']}")
                return

            return _sync_to_parent(_g, _v, _r, name, namespace, meta,
                                   *args, **kwargs)

        def on_child_delete(body, name, namespace,
                            *args, **kwargs):
            _, _ = args, kwargs

            _g, _v, _r = util.gvr_from_body(body)

            # remove watch
            gvr_str = util.gvr(_g, _v, _r)
            nsn_str = util.spaced_name(name, namespace)

            w = self._children_watches.get(gvr_str, {}).get(nsn_str, None)
            if w is not None:
                w.stop()
                self._children_watches[gvr_str].pop(nsn_str, "")

            # will delete from parent
            _sync_to_parent(_g, _v, _r, name, namespace, spec=None,
                            *args, **kwargs)

        def _sync_from_parent(group, version, plural, name, namespace, meta,
                              attrs_to_trim=None, *args, **kwargs):
            _, _ = args, kwargs

            parent, prv, pgn = util.get_spec(g, v, r, n, ns)

            # check if child exists
            mounts = parent.get("mount", {})
            gvr_str = util.gvr(group, version, plural)
            nsn_str = util.spaced_name(name, namespace)

            if (gvr_str not in mounts or
                    (nsn_str not in mounts[gvr_str] and
                     name not in mounts[gvr_str])):
                self._logger.warning(f"unable to find the {nsn_str} or {name} in the {parent}")
                return

            models = mounts[gvr_str]
            n_ = name if name in models else nsn_str

            patch = models[n_]
            if attrs_to_trim is not None:
                patch = util.trim_attr(patch, attrs_to_trim)

            _, resp, e = util.check_gen_and_patch_spec(
                group, version, plural,
                name, namespace,
                patch, gen=meta["generation"]
            )

            if e is not None:
                self._logger.warning(f"unable to sync from parent to {name} due to {e}")
            else:
                model_id = util.model_id(group, version, plural,
                                         name, namespace)
                new_gen = resp["metadata"]["generation"]
                self._children_gen[model_id] = new_gen
                if meta["generation"] + 1 == new_gen:
                    self._children_skip_gen[model_id] = new_gen

        def _sync_to_parent(group, version, plural, name, namespace, meta,
                            spec, diff, attrs_to_trim=None, *args, **kwargs):
            _, _ = args, kwargs

            # propagation from child retries until succeed
            while True:
                parent, prv, pgn = util.get_spec(g, v, r, n, ns)

                # check if child exists
                mounts = parent.get("mount", {})
                gvr_str = util.gvr(group, version, plural)
                nsn_str = util.spaced_name(name, namespace)

                if (gvr_str not in mounts or
                        (nsn_str not in mounts[gvr_str] and
                         name not in mounts[gvr_str])):
                    self._logger.warning(f"unable to find the {nsn_str} or {name} in the {parent}")
                    return

                models = mounts[gvr_str]
                n_ = name if name in models else nsn_str

                if spec is None:
                    parent_patch = None  # will convert to json null
                else:
                    if models[n_].get("mode", "hide") == "hide":
                        if attrs_to_trim is None:
                            attrs_to_trim = set()
                        attrs_to_trim.add("mount")

                    # TBD rename to _gen_parent_spec
                    parent_patch = _gen_parent_patch(spec, diff, attrs_to_trim)

                # add roots
                if parent_patch is None:
                    # only child
                    if len(mounts[gvr_str]) == 1:
                        parent_patch = {
                            "mount": {
                                gvr_str: None
                            }
                        }
                    else:
                        parent_patch = {
                            "mount": {
                                gvr_str: {
                                    n_: None
                                }
                            }
                        }
                else:
                    parent_patch = {
                        "mount": {
                            gvr_str: {
                                n_: {
                                    "spec": parent_patch,
                                    "generation": meta["generation"],
                                }
                            }
                        }}

                # maybe rejected if parent has been updated;
                # continue to try until succeed
                resp, e = util.patch_spec(g, v, r, n, ns, parent_patch, rv=prv)
                if e is not None:
                    if e.status == 409:
                        self._logger.warning(f"unable to sync to parent from {name} due to conflict; retry")
                    else:
                        self._logger.error(f"failed to sync {name} to parent due to {e}; abort")
                        return
                else:
                    new_gen = resp["metadata"]["generation"]
                    self._logger.info(f"update child {name} generation to {meta['generation']}")
                    if pgn + 1 == new_gen:
                        self._parent_skip_gen = new_gen
                    break

        def _gen_parent_patch(child_spec, diff, attrs_to_trim=None):
            child_spec = dict(child_spec)

            if diff is not None:
                child_spec = util.apply_diff({"spec": child_spec}, diff)["spec"]

            if attrs_to_trim is not None:
                child_spec = util.trim_attr(child_spec, attrs_to_trim)

            return child_spec

        """ parent event handlers """

        def on_parent_create(spec, diff, *args, **kwargs):
            _, _ = args, kwargs
            _update_children_watches(spec.get("mount", {}))
            _sync_to_children(spec, diff)

        def on_mount_attr_update(spec, meta, diff, *args, **kwargs):
            _, _ = args, kwargs

            if meta["generation"] == self._parent_skip_gen:
                self._logger.info(f"skipped parent gen {self._parent_skip_gen}")
                return

            mounts = spec.get("mount", {})

            _update_children_watches(mounts)
            _sync_to_children(spec, diff)
            _prune_mounts(mounts, meta)

        def on_parent_delete(*args, **kwargs):
            _, _ = args, kwargs
            self.stop()

        def _prune_mounts(mounts, meta):
            rv = meta["resourceVersion"]
            while True:
                to_prune = list()
                for gvr_str, models in mounts.items():
                    if len(models) == 0:
                        to_prune.append(gvr_str)
                if len(to_prune) == 0:
                    return
                patch = {
                    "mounts": {
                        gvr_str: None for gvr_str in to_prune
                    }
                }
                _, e = util.patch_spec(g, v, r, n, ns, patch, rv=rv)
                if e is None:
                    self._logger.info(f"prune mount: {patch}")
                    return
                elif e.status != 409:
                    self._logger.warning(f"prune mount failed due to {e}")
                    return

                self._logger.info(f"prune mount will retry due to: {e}")
                spec, rv, _ = util.get_spec(g, v, r, n, ns)
                mounts = spec.get("mount", {})

        def _update_children_watches(mounts: dict):
            # iterate over mounts and add/trim child event watches
            # add watches
            for gvr_str, models in mounts.items():
                gvr = parse_gvr(gvr_str)  # child's gvr

                for nsn_str, m in models.items():
                    nsn = parse_spaced_name(nsn_str)
                    # in case default ns is omitted in the model
                    nsn_str = spaced_name(*nsn)

                    if gvr_str in self._children_watches and \
                            nsn_str in self._children_watches[gvr_str]:
                        continue

                    # TBD: add child event handlers
                    self._logger.info(f"new watch for child {nsn_str}")
                    self._children_watches[gvr_str][nsn_str] \
                        = Watch(*gvr, *nsn,
                                create_fn=on_child_create,
                                resume_fn=on_child_create,
                                update_fn=on_child_update,
                                delete_fn=on_child_delete,
                                log_level=log_level).start()

            # trim watches no longer needed
            for gvr_str, model_watches in self._children_watches.items():
                mw_to_delete = set()
                for nsn_str, w in model_watches.items():
                    models = mounts.get(gvr_str, {})
                    if nsn_str not in models and \
                            util.trim_default_space(nsn_str) not in models:
                        w.stop()
                        mw_to_delete.add(nsn_str)

                for d in mw_to_delete:
                    model_watches.pop(d, None)

        def _gen_child_patch(parent_spec, gvr_str, nsn_str):
            mount_entry = parent_spec \
                .get("mount", {}) \
                .get(gvr_str, {}) \
                .get(nsn_str, {})
            if mount_entry.get("mode", "hide") == "hide":
                mount_entry.get("spec", {}).pop("mount", {})

            if mount_entry.get("status", "inactive") == "active":
                spec = mount_entry.get("spec", None)
                if spec is not None:
                    spec = util.trim_attr(spec, TRIM_FROM_PARENT)

                gen = mount_entry.get("generation", sys.maxsize)
                return spec, gen

            return None, None

        def _sync_to_children(parent_spec, diff):
            # sort the diff by the attribute path (in tuple)
            diff = sorted(diff, key=lambda x: x[1])

            # filter to only the intent/input updates
            to_sync = dict()
            for _, f, _, _ in diff:
                # skip non children update
                if len(f) < 3:
                    continue

                gvr_str, nsn_str = f[0], f[1]
                model_id = util.model_id(*parse_gvr(gvr_str),
                                         *parse_spaced_name(nsn_str))

                if model_id not in to_sync:
                    cs, gen = _gen_child_patch(parent_spec, gvr_str, nsn_str)
                    if cs is not None:
                        to_sync[model_id] = cs, gen

            # sync all, e.g., on parent resume and creation
            if len(diff) == 0:
                for gvr_str, ms in parent_spec.get("mount", {}).items():
                    for nsn_str, m in ms.items():
                        model_id = util.model_id(*parse_gvr(gvr_str),
                                                 *parse_spaced_name(nsn_str))
                        cs, gen = _gen_child_patch(parent_spec, gvr_str, nsn_str)
                        # both rv and gen can be none as during the initial sync
                        # the parent may overwrite
                        if cs is not None:
                            to_sync[model_id] = cs, gen

            # push to children models
            # TBD: transactional update
            for model_id, (cs, gen) in to_sync.items():
                cur_gen, resp, e = util.check_gen_and_patch_spec(
                    *util.parse_model_id(model_id),
                    spec=cs,
                    gen=max(gen, self._children_gen.get(model_id, -1)))
                if e is not None:
                    self._logger.warning(f"unable to sync to child {model_id} due to {e}")
                else:
                    new_gen = resp["metadata"]["generation"]
                    self._children_gen[model_id] = new_gen
                    if cur_gen + 1 == new_gen:
                        self._children_skip_gen[model_id] = new_gen

        # subscribe to the events of the parent model
        self._parent_watch = Watch(g, v, r, n, ns,
                                   create_fn=on_parent_create,
                                   resume_fn=on_parent_create,
                                   field_fn=on_mount_attr_update, field="spec.mount",
                                   delete_fn=on_parent_delete, delete_optional=True,
                                   log_level=log_level)

        # subscribe to the events of the child models;
        # keyed by the gvr and then spaced name
        self._children_watches = defaultdict(dict)

        # last handled generation of a child, keyed by model_id;
        # used when update the children because the parent's copy
        # might be out of date
        self._children_gen = dict()

        # used to filter last self-write on the child
        self._children_skip_gen = dict()
        self._parent_skip_gen = -1

        # mounter logging
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(log_level)

    def start(self):
        self._parent_watch.start()
        self._logger.info("started the mounter")

    def stop(self):
        self._parent_watch.stop()
        for _, mws in self._children_watches.items():
            for _, w in mws.items():
                w.stop()
        return self


def test():
    gvr = ("mock.digi.dev", "v1", "samples")
    Mounter(*gvr, n="sample").start()


if __name__ == '__main__':
    test()
