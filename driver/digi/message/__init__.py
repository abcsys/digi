import os
import logging

"""
The digi.message module provides the ability for digi developers to
ingest data from the built-in dSpace EMQX broker via MQTT. The driver
automatically listens on the topic corresponding to the digi's name,
and any JSON data that it receives will be added to the zed pool.
"""

from digi.message.mqtt import start_listening

__all__ = ["start_listening"]
