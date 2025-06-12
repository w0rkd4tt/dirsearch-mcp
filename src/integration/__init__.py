"""
Integration module for Dirsearch MCP
Provides interfaces for third-party tool integration
"""

from .interface import DirsearchMCP
from .plugin_base import Plugin, PluginManager
from .events import EventHook, EventType
from .data_formats import ScanData, TargetData, ResultData, ScanOptions

__all__ = [
    'DirsearchMCP',
    'Plugin',
    'PluginManager',
    'EventHook',
    'EventType',
    'ScanData',
    'TargetData',
    'ResultData',
    'ScanOptions'
]