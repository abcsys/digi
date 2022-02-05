import kopf

import digi.util as util
from digi.mount import Mounter


def run():
    import digi

    # mounter
    if digi.enable_mounter:
        Mounter(digi.g, digi.v, digi.r, digi.n, digi.ns,
                log_level=digi.log_level).start()
    # pool client
    digi.pool = digi.state.create_pool()
    digi.model = digi.state.create_model()

    # reconciler
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
        digi.logger.debug(f"processing gen: {meta['generation']}; "
                          f"resource version: {meta['resourceVersion']}; "
                          f"skip_gen: {rc.skip_gen}; "
                          f"last_seen_gen: {rc.last_seen_gen}; "
                          f"reconcile count: {rc.count}")

        gen = meta["generation"]
        if gen == rc.last_seen_gen:
            digi.logger.info(f"skipped gen {gen} due to last-seen")
            return

        rc.last_seen_gen = gen
        rc.count += 1

        if digi.pool is not None:
            try:
                model = CleanView(dict(spec),
                                  trim_mount=digi.load_trim_mount).m()
                model["_type"] = "model"
                digi.pool.load([model])
                digi.logger.info(f"done loading model snapshot to pool")
            except Exception as e:
                digi.logger.warning(f"unable to load to pool: {e}")

        # skip the last self-write
        # TBD for parallel reconciliation may need to lock rc.gen before patch
        if gen == rc.skip_gen:
            digi.logger.info(f"skipped gen {gen} due to self-write")
            return

        spec = rc.run(spec, *args, **kwargs)
        _, resp, e = util.check_gen_and_patch_spec(digi.g, digi.v, digi.r, digi.n, digi.ns,
                                                   spec, gen=gen)
        if e is not None:
            if e.status == util.DriverError.GEN_OUTDATED:
                digi.logger.warning(f"gen {gen} outdated; "
                                    f"pending {len(rc._pending_handler)} handlers")
                return
            else:
                raise kopf.PermanentError(e.status)

        # if the model isn't updated do not
        # increment the skip marker
        new_gen = resp["metadata"]["generation"]
        if gen + 1 == new_gen:
            rc.skip_gen = new_gen

        rc.clear_pending()
        digi.logger.info(f"done reconciliation")

    @kopf.on.delete(**_model, **_kwargs, optional=True)
    def on_delete(*args, **kwargs):
        _, _ = args, kwargs
        _stop.set()

    if digi.enable_visual:
        import os, sys, subprocess
        try:
            subprocess.check_call(f"python visual.py &",
                                  env={**os.environ.copy(), **{
                                      "MOUNTER": "false",
                                      "VISUAL": "false",
                                      "LOGGER_NAME": "digi.visual",
                                  }},
                                  shell=True)
            digi.logger.info("started visualizer")
        except subprocess.CalledProcessError:
            digi.logger.fatal("unable to start visualizer")
            sys.exit(1)

    # TBD graceful termination
    _ready, _stop = util.run_operator(_registry, log_level=digi.log_level)
