import os
import logging

# default logger
logger = logging.getLogger(os.environ.get("LOGGER_NAME", __name__))
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
load_trim_mount = os.environ.get("TRIM_MOUNT_ON_LOAD", "") != "false"
enable_mounter = os.environ.get("MOUNTER", "") == "true"
enable_visual = os.environ.get("VISUAL", "") == "true"
visual_type = os.environ.get("VISUAL_TYPE", "")
visual_refresh_interval = float(os.environ.get("VISUAL_REFRESH_INTERVAL", 1000))

# digi modules; force init
from digi import (
    on,
    util,
    mount,
    filter,
    view,
)
from digi.main import run
from digi.state import pool, model
from digi.reconcile import rc

__all__ = [
    "on", "util", "view", "filter",
    "run", "logger", "mount", "pool", "rc"
]
