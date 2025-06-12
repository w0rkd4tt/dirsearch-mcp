"""
Event system for Dirsearch MCP
Provides event hooks and event types
"""

import asyncio
from enum import Enum
from typing import List, Callable, Any, Coroutine
import inspect


class EventType(Enum):
    """Event types for Dirsearch MCP"""
    SCAN_STARTED = "scan_started"
    SCAN_COMPLETED = "scan_completed"
    TARGET_ANALYZED = "target_analyzed"
    FINDING_DISCOVERED = "finding_discovered"
    ERROR_OCCURRED = "error_occurred"
    PROGRESS_UPDATE = "progress_update"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"


class EventHook:
    """
    Event hook implementation
    Allows registration and firing of event handlers
    
    Example:
        hook = EventHook()
        
        # Register sync handler
        hook += lambda data: print(f"Event: {data}")
        
        # Register async handler
        async def async_handler(data):
            await asyncio.sleep(1)
            print(f"Async event: {data}")
        
        hook += async_handler
        
        # Fire event
        await hook.fire({'message': 'Hello'})
    """
    
    def __init__(self):
        """Initialize event hook"""
        self._handlers: List[Callable] = []
        
    def __iadd__(self, handler: Callable):
        """Add a handler using += operator"""
        self.register(handler)
        return self
        
    def __isub__(self, handler: Callable):
        """Remove a handler using -= operator"""
        self.unregister(handler)
        return self
        
    def register(self, handler: Callable):
        """
        Register an event handler
        
        Args:
            handler: Callable to handle the event
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            
    def unregister(self, handler: Callable):
        """
        Unregister an event handler
        
        Args:
            handler: Handler to remove
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            
    def clear(self):
        """Remove all handlers"""
        self._handlers.clear()
        
    async def fire(self, data: Any = None):
        """
        Fire the event to all handlers
        
        Args:
            data: Data to pass to handlers
        """
        tasks = []
        
        for handler in self._handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    # Async handler
                    task = asyncio.create_task(handler(data))
                    tasks.append(task)
                else:
                    # Sync handler - run in executor
                    loop = asyncio.get_event_loop()
                    task = loop.run_in_executor(None, handler, data)
                    tasks.append(task)
            except Exception as e:
                print(f"Error in event handler: {e}")
                
        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
    def handler_count(self) -> int:
        """Get number of registered handlers"""
        return len(self._handlers)


class EventEmitter:
    """
    Event emitter mixin class
    
    Example:
        class MyClass(EventEmitter):
            def __init__(self):
                super().__init__()
                self.register_event('my_event')
                
            async def do_something(self):
                await self.emit('my_event', {'data': 'value'})
    """
    
    def __init__(self):
        """Initialize event emitter"""
        self._events: Dict[str, EventHook] = {}
        
    def register_event(self, event_name: str):
        """
        Register a new event type
        
        Args:
            event_name: Name of the event
        """
        if event_name not in self._events:
            self._events[event_name] = EventHook()
            
    def on(self, event_name: str, handler: Callable):
        """
        Register an event handler
        
        Args:
            event_name: Name of the event
            handler: Handler function
        """
        if event_name not in self._events:
            self.register_event(event_name)
        self._events[event_name].register(handler)
        
    def off(self, event_name: str, handler: Callable):
        """
        Unregister an event handler
        
        Args:
            event_name: Name of the event
            handler: Handler function
        """
        if event_name in self._events:
            self._events[event_name].unregister(handler)
            
    async def emit(self, event_name: str, data: Any = None):
        """
        Emit an event
        
        Args:
            event_name: Name of the event
            data: Data to pass to handlers
        """
        if event_name in self._events:
            await self._events[event_name].fire(data)
            
    def once(self, event_name: str, handler: Callable):
        """
        Register a one-time event handler
        
        Args:
            event_name: Name of the event
            handler: Handler function
        """
        async def wrapper(data):
            await handler(data) if inspect.iscoroutinefunction(handler) else handler(data)
            self.off(event_name, wrapper)
            
        self.on(event_name, wrapper)