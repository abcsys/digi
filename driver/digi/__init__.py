import os
import logging
from kopf.engines import loggers

# default log level and format
logger = logging.getLogger(__name__)
__handler = logging.StreamHandler()
__handler.setFormatter(loggers.make_formatter())
logger.addHandler(__handler)
logger.setLevel(int(os.environ.get("LOGLEVEL", logging.INFO)))


# default auri
def set_default_gvr():
    if "GROUP" not in os.environ:
        os.environ["GROUP"] = "nil.digi.dev"
    if "VERSION" not in os.environ:
        os.environ["VERSION"] = "v0"
    if "PLURAL" not in os.environ:
        os.environ["PLURAL"] = "nil"
    if "NAME" not in os.environ:
        os.environ["NAME"] = "nil"
    if "NAMESPACE" not in os.environ:
        os.environ["NAMESPACE"] = "default"


set_default_gvr()


# digi modules
from digi import (
    on,
    util,
    view,
    filter,
    mount,
)
from digi.main import run
from digi.reconcile import rc
auri = (rc.g, rc.v, rc.r, rc.n, rc.ns)


__all__ = [
    "on", "util", "view", "filter",
    "run", "logger", "auri", "mount"
]
