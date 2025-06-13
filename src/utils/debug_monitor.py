"""
Real-time debug monitor for dirsearch engine scanning
Provides live monitoring of directory scanning, request/response details, and analysis
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.markdown import Markdown


class EventType(Enum):
    """Types of scan events"""
    SCAN_START = "scan_start"
    SCAN_END = "scan_end"
    REQUEST_SENT = "request_sent"
    RESPONSE_RECEIVED = "response_received"
    WILDCARD_DETECTED = "wildcard_detected"
    PATH_FILTERED = "path_filtered"
    DIRECTORY_FOUND = "directory_found"
    FILE_FOUND = "file_found"
    ERROR_OCCURRED = "error_occurred"
    RECURSION_START = "recursion_start"
    RECURSION_END = "recursion_end"
    MCP_DECISION = "mcp_decision"
    STATUS_CODE_CHECK = "status_code_check"


@dataclass
class DebugEvent:
    """Debug event data structure"""
    timestamp: float
    event_type: EventType
    url: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    response_size: Optional[int] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "url": self.url,
            "path": self.path,
            "status_code": self.status_code,
            "response_size": self.response_size,
            "response_time": self.response_time,
            "error": self.error,
            "metadata": self.metadata
        }


class DebugMonitor:
    """Real-time debug monitor for scan engine"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.events: List[DebugEvent] = []
        self.start_time: Optional[float] = None
        self.current_target: Optional[str] = None
        self.stats = {
            "total_requests": 0,
            "successful_responses": 0,
            "errors": 0,
            "directories_found": 0,
            "files_found": 0,
            "filtered_paths": 0,
            "wildcard_hits": 0,
            "status_codes": {}
        }
        self.filters = {
            "event_types": set(EventType),
            "min_status_code": None,
            "max_status_code": None,
            "path_pattern": None,
            "show_errors_only": False
        }
        self.callbacks: Dict[EventType, List[Callable]] = {event_type: [] for event_type in EventType}
        self.live_display: Optional[Live] = None
        self.is_monitoring = False
        
    def start_monitoring(self, target: str, live_display: bool = True):
        """Start monitoring a scan"""
        self.start_time = time.time()
        self.current_target = target
        self.is_monitoring = True
        
        if live_display:
            layout = self._create_layout()
            self.live_display = Live(layout, console=self.console, refresh_per_second=4)
            self.live_display.start()
            
        self.log_event(EventType.SCAN_START, metadata={"target": target})
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
            
        self.log_event(EventType.SCAN_END)
        
    def log_event(self, event_type: EventType, **kwargs):
        """Log a debug event"""
        event = DebugEvent(
            timestamp=time.time(),
            event_type=event_type,
            **kwargs
        )
        
        # Apply filters
        if not self._should_log_event(event):
            return
            
        self.events.append(event)
        self._update_stats(event)
        
        # Call registered callbacks
        for callback in self.callbacks[event_type]:
            try:
                callback(event)
            except Exception as e:
                self.console.print(f"[red]Callback error: {e}[/red]")
                
        # Update live display
        if self.live_display:
            self._update_display()
            
    def _should_log_event(self, event: DebugEvent) -> bool:
        """Check if event should be logged based on filters"""
        if event.event_type not in self.filters["event_types"]:
            return False
            
        if self.filters["show_errors_only"] and event.event_type != EventType.ERROR_OCCURRED:
            return False
            
        if event.status_code:
            if self.filters["min_status_code"] and event.status_code < self.filters["min_status_code"]:
                return False
            if self.filters["max_status_code"] and event.status_code > self.filters["max_status_code"]:
                return False
                
        if self.filters["path_pattern"] and event.path:
            import re
            if not re.search(self.filters["path_pattern"], event.path):
                return False
                
        return True
        
    def _update_stats(self, event: DebugEvent):
        """Update statistics based on event"""
        if event.event_type == EventType.REQUEST_SENT:
            self.stats["total_requests"] += 1
        elif event.event_type == EventType.RESPONSE_RECEIVED:
            self.stats["successful_responses"] += 1
            if event.status_code:
                self.stats["status_codes"][event.status_code] = self.stats["status_codes"].get(event.status_code, 0) + 1
        elif event.event_type == EventType.ERROR_OCCURRED:
            self.stats["errors"] += 1
        elif event.event_type == EventType.DIRECTORY_FOUND:
            self.stats["directories_found"] += 1
        elif event.event_type == EventType.FILE_FOUND:
            self.stats["files_found"] += 1
        elif event.event_type == EventType.PATH_FILTERED:
            self.stats["filtered_paths"] += 1
        elif event.event_type == EventType.WILDCARD_DETECTED:
            self.stats["wildcard_hits"] += 1
            
    def _create_layout(self) -> Layout:
        """Create the display layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="events", ratio=2)
        )
        
        return layout
        
    def _update_display(self):
        """Update the live display"""
        if not self.live_display:
            return
            
        layout = self.live_display.renderable
        
        # Update header
        elapsed = time.time() - self.start_time if self.start_time else 0
        header_text = f"[bold cyan]Dirsearch Debug Monitor[/bold cyan] | Target: [yellow]{self.current_target}[/yellow] | Elapsed: [green]{elapsed:.1f}s[/green]"
        layout["header"].update(Panel(header_text))
        
        # Update stats
        stats_table = Table(title="Statistics", box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Requests", str(self.stats["total_requests"]))
        stats_table.add_row("Successful", str(self.stats["successful_responses"]))
        stats_table.add_row("Errors", str(self.stats["errors"]))
        stats_table.add_row("Directories", str(self.stats["directories_found"]))
        stats_table.add_row("Files", str(self.stats["files_found"]))
        stats_table.add_row("Filtered", str(self.stats["filtered_paths"]))
        stats_table.add_row("Wildcards", str(self.stats["wildcard_hits"]))
        
        # Add status code breakdown
        if self.stats["status_codes"]:
            stats_table.add_row("", "")  # Empty row
            stats_table.add_row("[bold]Status Codes[/bold]", "")
            for code, count in sorted(self.stats["status_codes"].items()):
                color = self._get_status_color(code)
                stats_table.add_row(f"  {code}", f"[{color}]{count}[/{color}]")
                
        layout["stats"].update(Panel(stats_table, title="Scan Statistics"))
        
        # Update events
        events_text = self._format_recent_events()
        layout["events"].update(Panel(events_text, title="Recent Events"))
        
        # Update footer
        footer_text = f"Events: {len(self.events)} | Filters: {self._get_active_filters()}"
        layout["footer"].update(Panel(footer_text))
        
    def _format_recent_events(self, max_events: int = 20) -> Text:
        """Format recent events for display"""
        text = Text()
        recent_events = self.events[-max_events:]
        
        for event in recent_events:
            timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S.%f")[:-3]
            
            # Format based on event type
            if event.event_type == EventType.REQUEST_SENT:
                text.append(f"[{timestamp}] ", style="dim")
                text.append("→ ", style="blue")
                text.append(f"{event.path or event.url}\n", style="white")
                
            elif event.event_type == EventType.RESPONSE_RECEIVED:
                text.append(f"[{timestamp}] ", style="dim")
                text.append("← ", style="green")
                color = self._get_status_color(event.status_code)
                text.append(f"{event.status_code} ", style=color)
                text.append(f"{event.path} ", style="white")
                if event.response_time:
                    text.append(f"({event.response_time:.0f}ms) ", style="dim")
                if event.response_size:
                    text.append(f"[{event.response_size}B]\n", style="dim")
                else:
                    text.append("\n")
                    
            elif event.event_type == EventType.DIRECTORY_FOUND:
                text.append(f"[{timestamp}] ", style="dim")
                text.append("📁 ", style="yellow")
                text.append(f"Directory: {event.path}\n", style="yellow")
                
            elif event.event_type == EventType.FILE_FOUND:
                text.append(f"[{timestamp}] ", style="dim")
                text.append("📄 ", style="cyan")
                text.append(f"File: {event.path}\n", style="cyan")
                
            elif event.event_type == EventType.ERROR_OCCURRED:
                text.append(f"[{timestamp}] ", style="dim")
                text.append("❌ ", style="red")
                text.append(f"Error: {event.error}\n", style="red")
                
            elif event.event_type == EventType.WILDCARD_DETECTED:
                text.append(f"[{timestamp}] ", style="dim")
                text.append("🔍 ", style="magenta")
                text.append(f"Wildcard detected: {event.metadata}\n", style="magenta")
                
            elif event.event_type == EventType.PATH_FILTERED:
                text.append(f"[{timestamp}] ", style="dim")
                text.append("🚫 ", style="dim red")
                text.append(f"Filtered: {event.path} ", style="dim")
                if event.metadata.get("reason"):
                    text.append(f"({event.metadata['reason']})\n", style="dim")
                else:
                    text.append("\n")
                    
        return text
        
    def _get_status_color(self, status_code: Optional[int]) -> str:
        """Get color for status code"""
        if not status_code:
            return "white"
        elif 200 <= status_code < 300:
            return "green"
        elif 300 <= status_code < 400:
            return "yellow"
        elif 400 <= status_code < 500:
            return "red"
        elif 500 <= status_code < 600:
            return "bold red"
        else:
            return "white"
            
    def _get_active_filters(self) -> str:
        """Get active filters description"""
        filters = []
        if len(self.filters["event_types"]) < len(EventType):
            filters.append(f"Types: {len(self.filters['event_types'])}")
        if self.filters["min_status_code"] or self.filters["max_status_code"]:
            filters.append("Status")
        if self.filters["path_pattern"]:
            filters.append("Path")
        if self.filters["show_errors_only"]:
            filters.append("Errors Only")
            
        return ", ".join(filters) if filters else "None"
        
    def set_filter(self, filter_name: str, value: Any):
        """Set a filter"""
        if filter_name in self.filters:
            self.filters[filter_name] = value
            
    def register_callback(self, event_type: EventType, callback: Callable):
        """Register a callback for an event type"""
        self.callbacks[event_type].append(callback)
        
    def export_events(self, filepath: str, format: str = "json"):
        """Export events to file"""
        if format == "json":
            data = {
                "target": self.current_target,
                "start_time": self.start_time,
                "stats": self.stats,
                "events": [event.to_dict() for event in self.events]
            }
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            import csv
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "event_type", "url", "path", "status_code", "response_time", "error"])
                writer.writeheader()
                for event in self.events:
                    writer.writerow(event.to_dict())
                    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "target": self.current_target,
            "duration": elapsed,
            "total_events": len(self.events),
            "stats": self.stats,
            "requests_per_second": self.stats["total_requests"] / elapsed if elapsed > 0 else 0
        }
    
    def get_integration(self) -> 'DebugMonitorIntegration':
        """Get integration helper for dirsearch engine"""
        return DebugMonitorIntegration(self)


class DebugMonitorIntegration:
    """Integration helper for dirsearch engine"""
    
    def __init__(self, monitor: DebugMonitor):
        self.monitor = monitor
        
    async def wrap_request(self, url: str, path: str, request_func: Callable):
        """Wrap a request with monitoring"""
        start_time = time.time()
        
        # Log request sent
        self.monitor.log_event(
            EventType.REQUEST_SENT,
            url=url,
            path=path
        )
        
        try:
            # Execute request
            response = await request_func()
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Log response received
            self.monitor.log_event(
                EventType.RESPONSE_RECEIVED,
                url=url,
                path=path,
                status_code=response.status_code,
                response_size=len(response.content) if hasattr(response, 'content') else None,
                response_time=response_time
            )
            
            return response
            
        except Exception as e:
            # Log error
            self.monitor.log_event(
                EventType.ERROR_OCCURRED,
                url=url,
                path=path,
                error=str(e)
            )
            raise
            
    def log_wildcard_detection(self, url: str, wildcard_info: Dict[str, Any]):
        """Log wildcard detection"""
        self.monitor.log_event(
            EventType.WILDCARD_DETECTED,
            url=url,
            metadata=wildcard_info
        )
        
    def log_path_filtered(self, path: str, reason: str):
        """Log path filtering"""
        self.monitor.log_event(
            EventType.PATH_FILTERED,
            path=path,
            metadata={"reason": reason}
        )
        
    def log_discovery(self, url: str, path: str, is_directory: bool, status_code: int):
        """Log directory or file discovery"""
        event_type = EventType.DIRECTORY_FOUND if is_directory else EventType.FILE_FOUND
        self.monitor.log_event(
            event_type,
            url=url,
            path=path,
            status_code=status_code
        )
        
    def log_mcp_decision(self, decision: Dict[str, Any]):
        """Log MCP decision"""
        self.monitor.log_event(
            EventType.MCP_DECISION,
            metadata=decision
        )
        
    def log_recursion(self, directory: str, depth: int, starting: bool = True):
        """Log recursion event"""
        event_type = EventType.RECURSION_START if starting else EventType.RECURSION_END
        self.monitor.log_event(
            event_type,
            path=directory,
            metadata={"depth": depth}
        )