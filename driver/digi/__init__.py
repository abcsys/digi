import os
import logging

# default logger
logger = logging.getLogger(__name__)

# control the log level for k8s event and local/handler logging
log_level = int(os.environ.get("LOGLEVEL", logging.INFO))
logger.setLevel(log_level)

# digi metadata and identifiers
g = group = os.environ["GROUP"]
v = version = os.environ["VERSION"]
r = resource = os.environ["PLURAL"]
n = name = os.environ["NAME"]
ns = namespace = os.environ.get("NAMESPACE", "default")
auri = (g, v, r, n, ns)

pool_provider = os.environ.get("POOL_PROVIDER", "zed")

# digi modules; force init
from digi import (
    on,
    util,
    view,
    filter,
    mount,
)
from digi.main import run
from digi.pool import pool
from digi.reconcile import rc

__all__ = [
    "on", "util", "view", "filter",
    "run", "logger", "mount", "pool", "rc"
]
