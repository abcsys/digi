import os
import logging

# default logger
logger = logging.getLogger(__name__)

# control the log level for k8s event and local/handler logging
log_level = int(os.environ.get("LOGLEVEL", logging.INFO))
logger.setLevel(log_level)

# digi metadata and configurations
g = group = os.environ.get("GROUP", "digi.dev")
v = version = os.environ.get("VERSION", "v1")
r = resource = os.environ.get("PLURAL", "tests")
n = name = os.environ.get("NAME", "test")
ns = namespace = os.environ.get("NAMESPACE", "default")
duri = auri = (g, v, r, n, ns)

pool_provider = os.environ.get("POOL_PROVIDER", "zed")
enable_mounter = os.environ.get("MOUNTER", "false") == "true"
enable_viz = os.environ.get("VISUAL", "false") == "true"
load_trim_mount = os.environ.get("TRIM_MOUNT_ON_LOAD", "true") != "false"

# digi modules; force init
from digi import (
    on,
    util,
    mount,
    filter,
    view,
)
from digi.main import run
from digi.data import pool
from digi.reconcile import rc

__all__ = [
    "on", "util", "view", "filter",
    "run", "logger", "mount", "pool", "rc"
]
