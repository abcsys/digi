import kopf

import digi.util as util
from digi.mount import Mounter


def run():
    import digi

    # run mounter
    if digi.enable_mounter:
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
    from digi.view import CleanView

    @kopf.on.create(**_model, **_kwargs)
    @kopf.on.resume(**_model, **_kwargs)
    @kopf.on.update(**_model, **_kwargs)
    def reconcile(spec, meta, *args, **kwargs):
        gen = meta["generation"]
        digi.logger.info(f"processing gen {gen} skip_gen {rc.skip_gen}")

        if digi.pool is not None:
            try:
                model = CleanView(dict(spec),
                              trim_mount=digi.load_trim_mount).m()
                digi.pool.load([model])
                digi.logger.info(f"done loading model snapshot to pool")
            except Exception as e:
                digi.logger.warning(f"unable to load to pool: {e}")

        # skip the last self-write
        # TBD for parallel reconciliation may need to lock rc.gen before patch
        if gen == rc.skip_gen:
            digi.logger.info(f"skipped gen {gen}")
            return

        spec = rc.run(spec, *args, **kwargs)
        _, resp, e = util.check_gen_and_patch_spec(digi.g, digi.v, digi.r, digi.n, digi.ns,
                                                         spec, gen=gen)
        if e is not None:
            if e.status == util.DriverError.GEN_OUTDATED:
                # retry s.t. the diff object contains the past changes
                # TBD(@kopf) non-zero delay fix
                # raise kopf.TemporaryError(e, delay=0)
                digi.logger.warning(f"gen {gen} outdated; pending {len(rc._pending_handler)} handlers;")
                # fetch the latest and retry?
                return
            else:
                raise kopf.PermanentError(e.status)

        # if the model isn't updated do not
        # increment the skip marker
        new_gen = resp["metadata"]["generation"]
        digi.logger.info(f"new gen {new_gen} old gen {gen}")
        if gen + 1 == new_gen:
            rc.skip_gen = new_gen
        rc.clear_pending()
        digi.logger.info(f"done reconciliation")

    @kopf.on.delete(**_model, **_kwargs, optional=True)
    def on_delete(*args, **kwargs):
        _, _ = args, kwargs
        # _stop.set()

    _ready, _stop = util.run_operator(_registry, log_level=digi.log_level)

    if digi.enable_viz:
        import sys, subprocess
        try:
            subprocess.check_call("python ./driver/digi/visual.py >/dev/null 2>&1 &",
                                  shell=True)
        except subprocess.CalledProcessError:
            digi.logger.fatal("unable to start visualizer")
            sys.exit(1)
        digi.logger.info("started visualizer")
