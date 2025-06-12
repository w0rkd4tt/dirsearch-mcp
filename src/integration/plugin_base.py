"""
Plugin system for Dirsearch MCP
Provides base classes and plugin management
"""

import abc
import asyncio
import importlib.util
import inspect
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
import json
import sys

from .events import EventType
from .data_formats import ScanData, TargetData, ResultData


class Plugin(abc.ABC):
    """
    Base class for Dirsearch MCP plugins
    
    Example plugin:
        class MyPlugin(Plugin):
            name = "my_plugin"
            version = "1.0.0"
            description = "My custom plugin"
            
            async def on_scan_started(self, data):
                print(f"Scan started: {data['target']}")
                
            async def on_finding(self, finding):
                # Process finding
                if finding['status'] == 200:
                    await self.analyze_content(finding)
    """
    
    # Plugin metadata (override in subclass)
    name: str = "unnamed_plugin"
    version: str = "1.0.0"
    description: str = "No description"
    author: str = "Unknown"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin
        
        Args:
            config: Plugin configuration
        """
        self.config = config or {}
        self.enabled = True
        self._initialized = False
        
    @abc.abstractmethod
    async def initialize(self):
        """Initialize plugin (override in subclass)"""
        pass
    
    async def cleanup(self):
        """Cleanup plugin resources (override if needed)"""
        pass
    
    # Event handlers (override as needed)
    
    async def on_scan_started(self, data: Dict[str, Any]):
        """Called when scan starts"""
        pass
    
    async def on_scan_completed(self, scan_data: ScanData):
        """Called when scan completes"""
        pass
    
    async def on_target_analyzed(self, target_data: TargetData):
        """Called when target is analyzed"""
        pass
    
    async def on_finding(self, finding: Dict[str, Any]):
        """Called when a finding is discovered"""
        pass
    
    async def on_error(self, error_data: Dict[str, Any]):
        """Called when an error occurs"""
        pass
    
    async def on_progress(self, progress_data: Dict[str, Any]):
        """Called on progress updates"""
        pass
    
    # Utility methods for plugins
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        
    def log(self, message: str, level: str = "info"):
        """Log a message"""
        print(f"[{self.name}] {level.upper()}: {message}")
        
    def enable(self):
        """Enable the plugin"""
        self.enabled = True
        
    def disable(self):
        """Disable the plugin"""
        self.enabled = False
        
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.enabled


class PluginManager:
    """
    Manages plugins for Dirsearch MCP
    """
    
    def __init__(self):
        """Initialize plugin manager"""
        self.plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
        
    def register_plugin(self, plugin_class: Type[Plugin], 
                       config: Optional[Dict[str, Any]] = None):
        """
        Register a plugin class
        
        Args:
            plugin_class: Plugin class to register
            config: Optional plugin configuration
        """
        if not issubclass(plugin_class, Plugin):
            raise ValueError(f"{plugin_class} must be a subclass of Plugin")
            
        plugin_name = plugin_class.name
        self._plugin_classes[plugin_name] = plugin_class
        
        # Instantiate plugin
        plugin = plugin_class(config)
        self.plugins[plugin_name] = plugin
        
        print(f"Registered plugin: {plugin_name} v{plugin.version}")
        
    def load_plugin(self, plugin_path: str):
        """
        Load a plugin from file
        
        Args:
            plugin_path: Path to plugin file
        """
        path = Path(plugin_path)
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
            
        # Load module
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[path.stem] = module
        spec.loader.exec_module(module)
        
        # Find plugin classes
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                # Load config if exists
                config_path = path.with_suffix('.json')
                config = {}
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        
                self.register_plugin(obj, config)
                
    def load_plugins_from_directory(self, directory: str):
        """
        Load all plugins from a directory
        
        Args:
            directory: Directory containing plugin files
        """
        plugin_dir = Path(directory)
        if not plugin_dir.exists():
            return
            
        for file in plugin_dir.glob('*.py'):
            if file.name.startswith('_'):
                continue
            try:
                self.load_plugin(str(file))
            except Exception as e:
                print(f"Failed to load plugin {file.name}: {e}")
                
    async def initialize_plugins(self):
        """Initialize all registered plugins"""
        for name, plugin in self.plugins.items():
            if plugin.is_enabled() and not plugin._initialized:
                try:
                    await plugin.initialize()
                    plugin._initialized = True
                    print(f"Initialized plugin: {name}")
                except Exception as e:
                    print(f"Failed to initialize plugin {name}: {e}")
                    plugin.disable()
                    
    async def cleanup_plugins(self):
        """Cleanup all plugins"""
        for name, plugin in self.plugins.items():
            if plugin._initialized:
                try:
                    await plugin.cleanup()
                    print(f"Cleaned up plugin: {name}")
                except Exception as e:
                    print(f"Failed to cleanup plugin {name}: {e}")
                    
    async def notify_event(self, event_type: EventType, data: Dict[str, Any]):
        """
        Notify all plugins of an event
        
        Args:
            event_type: Type of event
            data: Event data
        """
        # Map event types to handler methods
        handlers = {
            EventType.SCAN_STARTED: 'on_scan_started',
            EventType.SCAN_COMPLETED: 'on_scan_completed',
            EventType.TARGET_ANALYZED: 'on_target_analyzed',
            EventType.FINDING_DISCOVERED: 'on_finding',
            EventType.ERROR_OCCURRED: 'on_error',
            EventType.PROGRESS_UPDATE: 'on_progress'
        }
        
        handler_name = handlers.get(event_type)
        if not handler_name:
            return
            
        # Convert data to appropriate type if needed
        if event_type == EventType.SCAN_COMPLETED and isinstance(data, dict):
            data = ScanData.from_dict(data)
        elif event_type == EventType.TARGET_ANALYZED and isinstance(data, dict):
            data = TargetData.from_dict(data)
            
        # Notify all enabled plugins
        tasks = []
        for plugin in self.plugins.values():
            if plugin.is_enabled() and plugin._initialized:
                handler = getattr(plugin, handler_name, None)
                if handler:
                    tasks.append(handler(data))
                    
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name"""
        return self.plugins.get(name)
        
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all registered plugins"""
        return [
            {
                'name': plugin.name,
                'version': plugin.version,
                'description': plugin.description,
                'author': plugin.author,
                'enabled': plugin.is_enabled(),
                'initialized': plugin._initialized
            }
            for plugin in self.plugins.values()
        ]
        
    def enable_plugin(self, name: str):
        """Enable a plugin by name"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enable()
            
    def disable_plugin(self, name: str):
        """Disable a plugin by name"""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.disable()