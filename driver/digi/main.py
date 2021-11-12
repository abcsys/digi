import os
import logging
import kopf

import digi.util as util
from digi.mount import Mounter


def run():
    g = os.environ["GROUP"]
    v = os.environ["VERSION"]
    r = os.environ["PLURAL"]
    n = os.environ["NAME"]
    ns = os.environ.get("NAMESPACE", "default")

    # control the log level for k8s event and local/handler logging
    log_level = int(os.environ.get("LOGLEVEL", logging.INFO))
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    # prevent printing root
    logging.getLogger().addHandler(logging.NullHandler())

    if os.environ.get("MOUNTER", "true") != "false":
        Mounter(g, v, r, n, ns, log_level=log_level).start()

    _model = {
        "group": g,
        "version": v,
        "plural": r,
    }
    _registry = util.KopfRegistry()
    _kwargs = {
        "when": lambda name, namespace, **_: name == n and namespace == ns,
        "registry": _registry,
    }
    _ready, _stop = None, None

    from . import handler  # decorate the handlers
    _ = handler

    @kopf.on.startup(registry=_registry)
    def configure(settings: kopf.OperatorSettings, **_):
        settings.persistence.progress_storage = kopf.AnnotationsProgressStorage()
        settings.posting.level = log_level

    from digi.reconcile import rc

    # TBD selectively add decorator

    @kopf.on.create(**_model, **_kwargs)
    @kopf.on.resume(**_model, **_kwargs)
    @kopf.on.update(**_model, **_kwargs)
    def reconcile(meta, *args, **kwargs):
        gen = meta["generation"]
        # skip the last self-write
        # TBD for parallel reconciliation may need to lock rc.gen before patch
        if gen == rc.skip_gen:
            logger.info(f"Skipping gen {gen}")
            return

        spec = rc.run(*args, **kwargs)
        _, resp, e = util.check_gen_and_patch_spec(g, v, r, n, ns,
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

    _ready, _stop = util.run_operator(_registry, log_level=log_level)
