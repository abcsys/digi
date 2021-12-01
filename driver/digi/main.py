import os
import logging
import kopf

import digi.util as util
from digi.mount import Mounter


def run():
    import digi

    logger = logging.getLogger(__name__)
    logger.setLevel(digi.log_level)

    # prevent printing root
    logging.getLogger().addHandler(logging.NullHandler())

    if os.environ.get("MOUNTER", "false") == "true":
        Mounter(digi.g, digi.v, digi.r, digi.n, digi.ns,
                log_level=digi.log_level).start()

    # kopf embedded operator
    _model = {
        "group": digi.g,
        "version": digi.v,
        "plural": digi.r,
    }
    _registry = util.KopfRegistry()
    _kwargs = {
        "when": lambda name, namespace, **_: name == digi.n and namespace == digi.ns,
        "registry": _registry,
    }
    _ready, _stop = None, None

    # force decorate the handlers
    from . import handler
    _ = handler

    @kopf.on.startup(registry=_registry)
    def configure(settings: kopf.OperatorSettings, **_):
        settings.persistence.progress_storage = kopf.AnnotationsProgressStorage()
        settings.posting.level = digi.log_level

    # reconciler operations
    from digi.reconcile import rc
    from digi.pool import pool
    from digi.view import CleanView
    _trim_mount = os.environ.get("PARENT_TRIM_MOUNT", True)

    # TBD selectively add decorator
    @kopf.on.create(**_model, **_kwargs)
    @kopf.on.resume(**_model, **_kwargs)
    @kopf.on.update(**_model, **_kwargs)
    def reconcile(spec, meta, *args, **kwargs):
        if pool is not None:
            try:
                pool.load([
                    CleanView(dict(spec), trim_mount=_trim_mount).m(),
                ])
                logger.info(f"Done loading model snapshot to pool.")
            except Exception as e:
                logger.warning(f"unable to load to pool: {e}")

        gen = meta["generation"]
        # skip the last self-write
        # TBD for parallel reconciliation may need to lock rc.gen before patch
        if gen == rc.skip_gen:
            logger.info(f"Skipping gen {gen}")
            return

        spec = rc.run(spec, *args, **kwargs)
        _, resp, e = util.check_gen_and_patch_spec(digi.g, digi.v, digi.r, digi.n, digi.ns,
                                                   spec, gen=gen)
        if e is not None:
            if e.status == util.DriverError.GEN_OUTDATED:
                # retry s.t. the diff object contains the past changes
                # TBD(@kopf) non-zero delay fix
                raise kopf.TemporaryError(e, delay=0)
            else:
                raise kopf.PermanentError(e.status)

        # if the model didn't get updated do not
        # increment the counter
        new_gen = resp["metadata"]["generation"]
        if gen + 1 == new_gen:
            rc.skip_gen = new_gen
        logger.info(f"Done reconciliation")

    @kopf.on.delete(**_model, **_kwargs, optional=True)
    def on_delete(*args, **kwargs):
        _, _ = args, kwargs
        # _stop.set()

    _ready, _stop = util.run_operator(_registry, log_level=digi.log_level)
