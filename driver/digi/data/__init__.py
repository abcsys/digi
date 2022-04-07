import os
import logging

logger = logging.getLogger(__name__)
os.environ["ZED_LAKE"] = os.environ.get("ZED_LAKE", "http://lake:6534")
lake_url = os.environ["ZED_LAKE"]

from digi.data.pool import create_pool
from digi.data.router import create_router
from digi.data.zed import Client
from digi.data.sync import Sync, Watch

_, _ = create_router, create_pool
_, _ = Sync, Watch
lake = Client()
