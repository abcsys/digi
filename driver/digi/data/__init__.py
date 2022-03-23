import os
import logging

os.environ["ZED_LAKE"] = os.environ.get("ZED_LAKE",
                                        "http://lake:6534")

logger = logging.getLogger(__name__)
from digi.data.pool import create_pool
from digi.data.router import create_router

_, _ = create_router, create_pool
