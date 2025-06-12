"""
Main integration interface for Dirsearch MCP
Provides a clean API for external tool integration
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
import json
from datetime import datetime
from dataclasses import dataclass, asdict

from src.config.settings import Settings
from src.core.dirsearch_engine import DirsearchEngine, ScanRequest, ScanResponse
from src.core.mcp_coordinator import MCPCoordinator
from src.utils.logger import LoggerSetup
from src.utils.reporter import ReportGenerator

from .plugin_base import PluginManager
from .events import EventHook, EventType
from .data_formats import ScanData, TargetData, ResultData, ScanOptions


class DirsearchMCP:
    """
    Main integration class for Dirsearch MCP
    
    Example usage:
        # Initialize
        dirsearch = DirsearchMCP()
        
        # Register event handlers
        dirsearch.on_finding(lambda data: print(f"Found: {data['path']}"))
        
        # Configure scan
        options = ScanOptions(
            threads=20,
            timeout=10,
            extensions=['php', 'html']
        )
        
        # Run scan
        results = await dirsearch.scan("https://example.com", options)
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize DirsearchMCP
        
        Args:
            config_file: Optional path to configuration file
        """
        self.settings = Settings(config_file)
        self.engine = DirsearchEngine(self.settings)
        self.mcp = MCPCoordinator(self.settings)
        self.logger = LoggerSetup.get_logger(__name__)
        self.reporter = ReportGenerator()
        
        # Plugin system
        self.plugin_manager = PluginManager()
        
        # Event hooks
        self.events = {
            EventType.SCAN_STARTED: EventHook(),
            EventType.SCAN_COMPLETED: EventHook(),
            EventType.TARGET_ANALYZED: EventHook(),
            EventType.FINDING_DISCOVERED: EventHook(),
            EventType.ERROR_OCCURRED: EventHook(),
            EventType.PROGRESS_UPDATE: EventHook()
        }
        
        # Initialize
        LoggerSetup.initialize()
        
    async def initialize(self):
        """Initialize MCP coordinator and plugins"""
        await self.mcp.initialize()
        await self.plugin_manager.initialize_plugins()
        
    # Core API methods
    
    async def scan(self, target: str, options: Optional[ScanOptions] = None) -> ScanData:
        """
        Perform a directory scan
        
        Args:
            target: Target URL to scan
            options: Optional scan configuration
            
        Returns:
            ScanData object with results
        """
        if options is None:
            options = ScanOptions()
            
        # Emit scan started event
        await self._emit_event(EventType.SCAN_STARTED, {
            'target': target,
            'options': asdict(options),
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            # Analyze target
            target_info = await self.analyze_target(target)
            
            # Generate scan plan
            if options.use_mcp:
                scan_plan = await self.mcp.generate_scan_plan(target_info._internal)
                params = await self.mcp.optimize_parameters(target_info._internal)
                
                # Update options with MCP recommendations
                options.threads = params.get('threads', options.threads)
                options.timeout = params.get('timeout', options.timeout)
            
            # Create scan request
            scan_request = ScanRequest(
                base_url=target,
                wordlist=options.wordlist,
                extensions=options.extensions,
                threads=options.threads,
                timeout=options.timeout,
                delay=options.delay,
                user_agent=options.user_agent,
                follow_redirects=options.follow_redirects,
                custom_headers=options.custom_headers,
                proxy=options.proxy,
                max_retries=options.max_retries,
                exclude_status=options.exclude_status,
                include_status=options.include_status
            )
            
            # Execute scan with progress tracking
            scan_response = await self._execute_scan_with_progress(scan_request)
            
            # Create scan data
            scan_data = ScanData(
                target=target,
                target_info=target_info,
                options=options,
                results=[ResultData.from_dict(r) for r in scan_response.results],
                statistics=scan_response.statistics,
                start_time=scan_response.statistics.get('start_time'),
                end_time=scan_response.statistics.get('end_time'),
                duration=scan_response.statistics.get('duration', 0),
                mcp_mode=self.mcp.intelligence_mode
            )
            
            # Emit scan completed event
            await self._emit_event(EventType.SCAN_COMPLETED, asdict(scan_data))
            
            return scan_data
            
        except Exception as e:
            # Emit error event
            await self._emit_event(EventType.ERROR_OCCURRED, {
                'error': str(e),
                'target': target,
                'timestamp': datetime.now().isoformat()
            })
            raise
    
    async def analyze_target(self, url: str) -> TargetData:
        """
        Analyze a target URL
        
        Args:
            url: Target URL to analyze
            
        Returns:
            TargetData object with target information
        """
        target_info = await self.mcp.analyze_target(url)
        
        target_data = TargetData(
            url=target_info.url,
            domain=target_info.domain,
            server_type=target_info.server_type,
            technology_stack=target_info.technology_stack,
            detected_cms=target_info.detected_cms,
            security_headers=target_info.security_headers,
            response_patterns=target_info.response_patterns
        )
        
        # Store internal reference for MCP
        target_data._internal = target_info
        
        # Emit target analyzed event
        await self._emit_event(EventType.TARGET_ANALYZED, asdict(target_data))
        
        return target_data
    
    async def generate_report(self, scan_data: ScanData, 
                            output_dir: str = "./reports",
                            formats: List[str] = ["json", "html", "markdown"]) -> Dict[str, str]:
        """
        Generate scan reports
        
        Args:
            scan_data: Scan data to report
            output_dir: Output directory for reports
            formats: List of report formats
            
        Returns:
            Dictionary mapping format to file path
        """
        # Convert to internal format
        report_data = {
            'target_url': scan_data.target,
            'target_domain': scan_data.target_info.domain,
            'start_time': scan_data.start_time,
            'end_time': scan_data.end_time,
            'duration': scan_data.duration,
            'intelligence_mode': scan_data.mcp_mode,
            'target_analysis': asdict(scan_data.target_info),
            'scan_results': [{
                'task_id': 'api_scan',
                'status': 'completed',
                'findings': [asdict(r) for r in scan_data.results],
                'metrics': scan_data.statistics,
                'timestamp': scan_data.end_time
            }],
            'performance_metrics': {
                'total_requests': scan_data.statistics.get('total_requests', 0),
                'found_paths': scan_data.statistics.get('found_paths', 0),
                'errors': scan_data.statistics.get('errors', 0)
            }
        }
        
        self.reporter.output_dir = output_dir
        return self.reporter.generate_report(report_data, format='all' if len(formats) > 1 else formats[0])
    
    # Plugin management
    
    def register_plugin(self, plugin_class: type, config: Optional[Dict[str, Any]] = None):
        """
        Register a plugin
        
        Args:
            plugin_class: Plugin class to register
            config: Optional plugin configuration
        """
        self.plugin_manager.register_plugin(plugin_class, config)
    
    def load_plugin(self, plugin_path: str):
        """
        Load a plugin from file
        
        Args:
            plugin_path: Path to plugin file
        """
        self.plugin_manager.load_plugin(plugin_path)
    
    # Event handling
    
    def on_scan_started(self, handler: Callable):
        """Register handler for scan started event"""
        self.events[EventType.SCAN_STARTED] += handler
        
    def on_scan_completed(self, handler: Callable):
        """Register handler for scan completed event"""
        self.events[EventType.SCAN_COMPLETED] += handler
        
    def on_target_analyzed(self, handler: Callable):
        """Register handler for target analyzed event"""
        self.events[EventType.TARGET_ANALYZED] += handler
        
    def on_finding(self, handler: Callable):
        """Register handler for finding discovered event"""
        self.events[EventType.FINDING_DISCOVERED] += handler
        
    def on_error(self, handler: Callable):
        """Register handler for error event"""
        self.events[EventType.ERROR_OCCURRED] += handler
        
    def on_progress(self, handler: Callable):
        """Register handler for progress update event"""
        self.events[EventType.PROGRESS_UPDATE] += handler
    
    # Configuration methods
    
    def set_mcp_mode(self, mode: str):
        """
        Set MCP intelligence mode
        
        Args:
            mode: 'auto', 'local', or 'ai'
        """
        if mode == 'local':
            self.mcp.intelligence_mode = 'LOCAL'
        elif mode == 'ai':
            self.mcp.intelligence_mode = 'AI_AGENT'
        # 'auto' will be determined by initialize()
            
    def set_ai_credentials(self, provider: str, api_key: str, model: Optional[str] = None):
        """
        Set AI provider credentials
        
        Args:
            provider: 'openai' or 'deepseek'
            api_key: API key
            model: Optional model name
        """
        if provider == 'openai':
            self.settings.ai_config['openai_api_key'] = api_key
            if model:
                self.settings.ai_config['openai_model'] = model
        elif provider == 'deepseek':
            self.settings.ai_config['deepseek_api_key'] = api_key
            if model:
                self.settings.ai_config['deepseek_model'] = model
    
    def configure(self, **kwargs):
        """
        Configure scan settings
        
        Args:
            **kwargs: Configuration parameters
        """
        for key, value in kwargs.items():
            if hasattr(self.settings.default_scan_config, key):
                self.settings.default_scan_config[key] = value
    
    # Utility methods
    
    async def get_wordlists(self) -> List[Dict[str, str]]:
        """Get available wordlists"""
        wordlists_dir = Path(self.settings.paths.get('wordlists', 'wordlists'))
        wordlists = []
        
        if wordlists_dir.exists():
            for file in wordlists_dir.glob('*.txt'):
                wordlists.append({
                    'name': file.name,
                    'path': str(file),
                    'size': file.stat().st_size
                })
                
        return wordlists
    
    async def validate_target(self, url: str) -> bool:
        """
        Validate if a target is accessible
        
        Args:
            url: Target URL
            
        Returns:
            True if target is accessible
        """
        try:
            target_info = await self.analyze_target(url)
            return target_info is not None
        except:
            return False
    
    # Private methods
    
    async def _execute_scan_with_progress(self, scan_request: ScanRequest) -> ScanResponse:
        """Execute scan with progress tracking"""
        # Create a wrapper to emit progress events
        original_execute = self.engine.execute_scan
        
        async def progress_wrapper(request):
            # Start progress tracking
            total_paths = len(self.engine._load_wordlist(request.wordlist))
            processed = 0
            
            # Execute scan
            response = await original_execute(request)
            
            # Emit progress updates periodically
            for i, result in enumerate(response.results):
                processed += 1
                if processed % 10 == 0:  # Update every 10 paths
                    await self._emit_event(EventType.PROGRESS_UPDATE, {
                        'processed': processed,
                        'total': total_paths,
                        'percentage': (processed / total_paths) * 100,
                        'current_path': result.get('path', '')
                    })
                
                # Emit finding event
                if result.get('status', 0) in [200, 201, 301, 302, 401, 403]:
                    await self._emit_event(EventType.FINDING_DISCOVERED, result)
            
            return response
        
        return await progress_wrapper(scan_request)
    
    async def _emit_event(self, event_type: EventType, data: Dict[str, Any]):
        """Emit an event to all registered handlers"""
        if event_type in self.events:
            await self.events[event_type].fire(data)
            
            # Also notify plugins
            await self.plugin_manager.notify_event(event_type, data)
    
    # Context manager support
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Cleanup if needed
        pass