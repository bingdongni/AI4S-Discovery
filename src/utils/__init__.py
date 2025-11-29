#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工具模块"""

from .device_manager import device_manager, DeviceManager
from .logger_config import setup_logger, get_logger

__all__ = ["device_manager", "DeviceManager", "setup_logger", "get_logger"]