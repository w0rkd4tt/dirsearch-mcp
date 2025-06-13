import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from urllib.parse import urljoin, urlparse, unquote
import time
import re
import difflib
import random
import string
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
import queue
import csv
import io
import json
from datetime import datetime

import httpx
from httpx import AsyncClient, Response as HttpxResponse, DigestAuth
try:
    import aiohttp
    from aiohttp import ClientSession, ClientResponse
except ImportError:
    aiohttp = None
    ClientSession = None
    ClientResponse = None
try:
    from httpx_ntlm import NTLMAuth
except ImportError:
    NTLMAuth = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from .intelligent_scanner import IntelligentScanner
from ..utils.debug_monitor import DebugMonitor, DebugMonitorIntegration, EventType


class DynamicContentParser:
    """Parser for detecting dynamic content in responses"""
    
    def __init__(self, content1: str, content2: str):
        self._static_patterns = None
        self._differ = difflib.Differ()
        self._is_static = content1 == content2
        self._base_content = content1
        
        if not self._is_static:
            self._static_patterns = self.get_static_patterns(
                self._differ.compare(content1.split(), content2.split())
            )
    
    def compare_to(self, content: str) -> bool:
        """Compare content to detect if it's similar to wildcard response"""
        if self._is_static:
            return content == self._base_content
        
        i = -1
        splitted_content = content.split()
        misses = 0
        
        for pattern in self._static_patterns:
            try:
                i = splitted_content.index(pattern, i + 1)
            except ValueError:
                if misses or len(self._static_patterns) < 20:
                    return False
                misses += 1
        
        # Check similarity ratio for reliability
        if len(content.split()) > len(self._base_content.split()) and len(self._static_patterns) < 20:
            return difflib.SequenceMatcher(None, self._base_content, content).ratio() > 0.75
        
        return True
    
    @staticmethod
    def get_static_patterns(patterns):
        """Get stable patterns from diff comparison"""
        return [pattern[2:] for pattern in patterns if pattern.startswith("  ")]


@dataclass
class ScanOptions:
    """Configuration options for directory scanning"""
    extensions: List[str] = field(default_factory=lambda: [])
    status_codes: List[int] = field(default_factory=lambda: [200, 204, 301, 302, 307, 401, 403])
    exclude_status_codes: List[int] = field(default_factory=lambda: [404])
    threads: int = 30
    timeout: int = 7
    delay: float = 0
    recursive: bool = False
    recursion_depth: int = 2
    force_extensions: bool = False
    exclude_extensions: List[str] = field(default_factory=lambda: [])
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    user_agent: str = "Mozilla/5.0 (compatible; Dirsearch)"
    # Debug options
    debug_enabled: bool = False
    debug_live_display: bool = True
    debug_export_path: Optional[str] = None
    proxy: Optional[str] = None
    auth: Optional[Tuple[str, str]] = None
    follow_redirects: bool = False  # Changed to False to capture 301 status
    exclude_sizes: List[int] = field(default_factory=lambda: [])
    exclude_texts: List[str] = field(default_factory=lambda: [])
    exclude_regex: Optional[str] = None
    include_status_codes: Optional[List[int]] = None
    retry_on_status: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    max_retries: int = 3
    subdirs: List[str] = field(default_factory=lambda: [])
    prefixes: List[str] = field(default_factory=lambda: [""])
    suffixes: List[str] = field(default_factory=lambda: [""])
    uppercase: bool = False
    lowercase: bool = False
    capitalization: bool = False
    # Enhanced features from original dirsearch
    auth_type: str = "basic"  # basic, digest, ntlm
    crawl: bool = False  # Enable crawling discovered pages
    detect_wildcards: bool = True  # Enable wildcard response detection
    random_user_agents: bool = False  # Use random user agents
    extension_tag: str = "%EXT%"  # Tag for extension replacement in wordlists
    blacklists: Dict[int, List[str]] = field(default_factory=dict)  # Status code blacklists


@dataclass
class ScanRequest:
    """Request configuration for a scan"""
    base_url: str
    wordlist: str
    extensions: List[str] = field(default_factory=list)
    threads: int = 10
    timeout: int = 10
    delay: float = 0
    user_agent: str = "Mozilla/5.0 (compatible; Dirsearch-MCP/1.0)"
    follow_redirects: bool = False  # Changed to False to capture 301 status
    custom_headers: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None
    max_retries: int = 3
    exclude_status: Optional[str] = "404"
    include_status: Optional[str] = None
    recursive: bool = True  # Default to True for recursive scanning
    recursion_depth: int = 3  # Default depth of 3 levels
    wordlist_type: str = "enhanced"  # Type of wordlist to use
    additional_wordlists: List[str] = field(default_factory=list)  # Additional wordlists to combine
    # Debug options
    debug_enabled: bool = False
    debug_live_display: bool = True
    debug_export_path: Optional[str] = None


@dataclass
class ScanResponse:
    """Response from a scan operation"""
    target_url: str
    results: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None


@dataclass
class ScanResult:
    """Individual scan result"""
    url: str
    status_code: int
    size: int
    redirect_url: Optional[str] = None
    content_type: Optional[str] = None
    response_time: float = 0
    timestamp: float = field(default_factory=time.time)
    path: str = ""
    is_directory: bool = False


@dataclass
class ScanStatistics:
    """Statistics for the scan session"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    filtered_results: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def requests_per_second(self) -> float:
        duration = self.duration
        return self.total_requests / duration if duration > 0 else 0


class DirsearchEngine:
    """Main engine for directory searching with dirsearch compatibility"""
    
    def __init__(self, settings=None, logger=None):
        self.settings = settings
        self.logger = logger
        self._executor = None
        self._session = None
        self._async_client = None
        self._stats = ScanStatistics()
        self._results: List[ScanResult] = []
        self._scanned_paths: Set[str] = set()
        self._progress_callback: Optional[Callable] = None
        self._result_callback: Optional[Callable] = None
        self._error_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._queue = queue.Queue()
        
        # Initialize intelligent scanner
        self.intelligent_scanner = IntelligentScanner()
        self._discovered_important_paths = []
        self._dynamic_wordlist = set()
        
        # Initialize recursive scan tracking
        self._deep_scanned_dirs = set()
        self._deep_analyzed_endpoints = set()
        self._recursive_scan_queue = set()
        
        # Default configuration
        self.config = settings.default_scan_config if settings else {
            'threads': 10,
            'timeout': 10,
            'user_agent': 'Mozilla/5.0 (compatible; Dirsearch-MCP/1.0)',
            'follow_redirects': False,  # Changed to False to capture 301 status
            'exclude_status': '404',
            'default_wordlist': 'wordlists/combined-enhanced.txt',
            'wordlists': {
                'common': 'wordlists/common.txt',
                'api': 'wordlists/api-endpoints.txt',
                'hidden': 'wordlists/hidden-files.txt',
                'enhanced': 'wordlists/combined-enhanced.txt',
                'monster': 'wordlists/monster-all.txt'
            }
        }
        
        # Enhanced features from original dirsearch
        self._wildcard_responses = {}
        self._dynamic_parsers = {}
        self._user_agents = []
        self._crawled_paths = set()
        self._blacklists = self._load_blacklists()
        
        # Debug monitor
        self.debug_monitor: Optional[DebugMonitor] = None
        self.debug_integration: Optional[DebugMonitorIntegration] = None
        
    async def __aenter__(self):
        if aiohttp and ClientSession:
            self._session = ClientSession()
        else:
            self._session = None
        self._async_client = httpx.AsyncClient()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def close(self):
        """Clean up resources"""
        if self._session:
            await self._session.close()
        if self._async_client:
            await self._async_client.aclose()
        if self._executor:
            self._executor.shutdown(wait=True)
            
    def set_progress_callback(self, callback: Callable[[int, int], None]):
        """Set callback for progress updates"""
        self._progress_callback = callback
        
    def set_result_callback(self, callback: Callable[[ScanResult], None]):
        """Set callback for new results"""
        self._result_callback = callback
        
    def set_error_callback(self, callback: Callable[[Exception], None]):
        """Set callback for errors"""
        self._error_callback = callback
        
    async def scan_target(
        self, 
        url: str, 
        wordlist: List[str], 
        options: Optional[ScanOptions] = None,
        display_progress: bool = True
    ) -> List[ScanResult]:
        """
        Main method to scan a target URL with given wordlist
        
        Args:
            url: Target URL to scan
            wordlist: List of paths to test
            options: Scan configuration options
            
        Returns:
            List of scan results
        """
        if options is None:
            options = ScanOptions()
            
        # Initialize debug monitor if enabled
        if options.debug_enabled:
            self.debug_monitor = DebugMonitor()
            self.debug_integration = DebugMonitorIntegration(self.debug_monitor)
            self.debug_monitor.start_monitoring(url, options.debug_live_display)
            
        # Reset state
        self._stats = ScanStatistics()
        self._results.clear()
        self._scanned_paths.clear()
        self._stop_event.clear()
        
        # Reset recursive scan tracking
        self._deep_scanned_dirs.clear()
        self._deep_analyzed_endpoints.clear()
        self._recursive_scan_queue.clear()
        
        # Store original wordlist for recursive scanning
        self._original_wordlist = wordlist.copy()
        
        # Store display preference
        self._display_progress = display_progress
        
        # Prepare URL
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        # Parse URL to check if it has a path that should be treated as a directory
        parsed = urlparse(url)
        if parsed.path and parsed.path != '/':
            # If path doesn't end with / and doesn't look like a file, add /
            if not parsed.path.endswith('/'):
                last_segment = parsed.path.split('/')[-1]
                # If no extension, likely a directory
                if '.' not in last_segment:
                    url = url + '/'
                    if self.logger:
                        self.logger.debug(f"Added trailing slash to directory URL: {url}")
        else:
            # For root URLs, ensure no trailing slash for consistency
            url = url.rstrip('/')
            
        # Detect wildcard responses if enabled
        wildcard_info = None
        if options.detect_wildcards:
            if self.logger:
                self.logger.info("Detecting wildcard responses...")
            wildcard_info = await self._detect_wildcard(url, options)
            if wildcard_info and wildcard_info.get('detected'):
                if self.logger:
                    self.logger.warning(f"Wildcard response detected for status {wildcard_info['status']}")
        
        # Store wildcard info for this URL
        self._wildcard_responses[url] = wildcard_info
        
        # Log wildcard detection with debug monitor
        if self.debug_integration and wildcard_info:
            self.debug_integration.log_wildcard_detection(url, wildcard_info)
        
        # Generate paths to scan
        paths = self._generate_paths(wordlist, options)
        
        # Start scanning
        if self.logger:
            self.logger.info(f"Starting scan on {url} with {len(paths)} paths")
            
        await self._scan_paths(url, paths, options)
        
        self._stats.end_time = time.time()
        
        # Stop debug monitoring and export if configured
        if self.debug_monitor:
            self.debug_monitor.stop_monitoring()
            
            # Export debug data if path specified
            if options.debug_export_path:
                self.debug_monitor.export_events(options.debug_export_path)
                if self.logger:
                    self.logger.info(f"Debug data exported to {options.debug_export_path}")
                    
            # Log summary
            summary = self.debug_monitor.get_summary()
            if self.logger:
                self.logger.info(f"Debug summary: {summary['total_events']} events, {summary['requests_per_second']:.2f} req/s")
        
        return self._results
        
    def _generate_paths(self, wordlist: List[str], options: ScanOptions) -> List[str]:
        """Generate all path combinations based on wordlist and options"""
        # First, handle extension tags if present
        if options.extension_tag and options.extensions:
            wordlist = self._enhance_wordlist_with_extensions(wordlist, options.extensions, options.extension_tag)
        
        paths = set()
        
        for word in wordlist:
            # Handle subdirectories
            for subdir in options.subdirs or ['']:
                base_path = f"{subdir}/{word}" if subdir else word
                
                # Handle prefixes and suffixes
                for prefix in options.prefixes:
                    for suffix in options.suffixes:
                        path = f"{prefix}{base_path}{suffix}"
                        
                        # Handle extensions (if not already handled by extension tag)
                        if options.extensions and options.extension_tag not in word:
                            for ext in options.extensions:
                                paths.add(f"{path}.{ext}")
                        else:
                            paths.add(path)
                            
                        # Handle case variations
                        if options.uppercase:
                            paths.add(path.upper())
                        if options.lowercase:
                            paths.add(path.lower())
                        if options.capitalization:
                            paths.add(path.capitalize())
                            
        return list(paths)
        
    async def _scan_paths(
        self, 
        base_url: str, 
        paths: List[str], 
        options: ScanOptions
    ):
        """Scan multiple paths concurrently"""
        semaphore = asyncio.Semaphore(options.threads)
        
        tasks = []
        for i, path in enumerate(paths):
            if self._stop_event.is_set():
                break
                
            task = asyncio.create_task(self._scan_single_path(
                base_url, path, options, semaphore, i, len(paths)
            ))
            tasks.append(task)
            
            # Add delay if specified
            if options.delay > 0:
                await asyncio.sleep(options.delay)
                
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            # Cancel all tasks when interrupted
            for task in tasks:
                if not task.done():
                    task.cancel()
            # Wait for tasks to complete cancellation
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        
        # Handle recursive scanning
        if options.recursive:
            await self._handle_recursive_scan(base_url, options)
            
    async def _scan_single_path(
        self,
        base_url: str,
        path: str,
        options: ScanOptions,
        semaphore: asyncio.Semaphore,
        current: int,
        total: int
    ) -> Optional[ScanResult]:
        """Scan a single path"""
        async with semaphore:
            # Construct full URL first
            url = urljoin(base_url, path)
            
            # Skip if already scanned (check full URL)
            with self._lock:
                if url in self._scanned_paths:
                    return None
                self._scanned_paths.add(url)
            
            # Debug logging for important paths
            if self.logger and 'admin' in path.lower():
                self.logger.debug(f"Scanning admin path: {path} -> {url}")
            
            # Update progress
            if self._progress_callback:
                self._progress_callback(current + 1, total)
            
            # Display real-time progress if enabled
            if hasattr(self, '_display_progress') and self._display_progress:
                print(f"[{current + 1}/{total}] Checking: {url} ...", end="", flush=True)
                
            # Perform request with retries
            for attempt in range(options.max_retries):
                try:
                    # Use debug monitor wrapper if available
                    if self.debug_integration:
                        response_data = await self.debug_integration.wrap_request(
                            url, path, 
                            lambda: self._make_request(url, options)
                        )
                    else:
                        response_data = await self._make_request(url, options)
                        
                    if response_data:
                        result = self.parse_response(url, path, response_data, options)
                        
                        # Display status code for each check if enabled
                        if hasattr(self, '_display_progress') and self._display_progress:
                            status = response_data.get('status_code', 0)
                            print(f" [{status}]")
                            
                            # Print found items immediately
                            if result and status not in [404]:
                                print(f"  ✓ Found: {path} - Status: {status} - Size: {response_data.get('size', 0)} bytes")
                        
                        if result and self._should_include_result(result, options):
                            with self._lock:
                                self._results.append(result)
                                self._stats.successful_requests += 1
                                
                                # Log discovery with debug monitor
                                if self.debug_integration:
                                    self.debug_integration.log_discovery(
                                        url, path, result.is_directory, result.status_code
                                    )
                                
                                # Intelligent analysis for important paths
                                # Skip 403 as they are forbidden
                                if result.status_code in [200, 301, 302]:
                                    self._analyze_and_expand(result)
                                
                                # Crawl response if enabled
                                if options.crawl and result.status_code == 200 and response_data:
                                    crawled_paths = await self._crawl_response(response_data, url)
                                    for crawled_path in crawled_paths:
                                        # Check if this path has been scanned in the current base URL context
                                        crawled_full_url = urljoin(base_url, crawled_path)
                                        if crawled_path not in self._crawled_paths and crawled_full_url not in self._scanned_paths:
                                            self._crawled_paths.add(crawled_path)
                                            self._dynamic_wordlist.add(crawled_path)
                                
                            if self._result_callback:
                                self._result_callback(result)
                                
                            return result
                        else:
                            with self._lock:
                                self._stats.filtered_results += 1
                                # Log filtered path with debug monitor
                                if self.debug_integration and result:
                                    reason = self._get_filter_reason(result, options)
                                    self.debug_integration.log_path_filtered(path, reason)
                                # Debug logging for filtered admin paths
                                if self.logger and result and 'admin' in result.path.lower():
                                    self.logger.debug(f"Admin path filtered: {result.path} (status: {result.status_code})")
                                
                    break
                    
                except asyncio.CancelledError:
                    # Re-raise cancellation
                    raise
                except Exception as e:
                    # Display error if progress is enabled
                    if hasattr(self, '_display_progress') and self._display_progress:
                        print(f" [ERROR: {str(e)}]")
                    raise
                except Exception as e:
                    if attempt == options.max_retries - 1:
                        with self._lock:
                            self._stats.failed_requests += 1
                            self._stats.errors.append({
                                'url': url,
                                'error': str(e),
                                'timestamp': time.time()
                            })
                            
                        if self._error_callback:
                            self._error_callback(e)
                            
                    else:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
            with self._lock:
                self._stats.total_requests += 1
                
        return None
        
    async def _make_request(
        self, 
        url: str, 
        options: ScanOptions
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request and return response data"""
        # Use random user agent if enabled
        user_agent = self._get_random_user_agent() if options.random_user_agents else options.user_agent
        
        headers = {
            'User-Agent': user_agent,
            **options.headers
        }
        
        # Get appropriate auth handler
        auth = None
        if options.auth:
            auth = self._get_auth_handler(options.auth_type, options.auth)
        
        start_time = time.time()
        
        try:
            # Build client kwargs
            client_kwargs = {
                'timeout': options.timeout,
                'follow_redirects': options.follow_redirects,
                'verify': False
            }
            
            # Only add proxy if it's provided
            if options.proxy:
                client_kwargs['proxies'] = options.proxy
            
            async with httpx.AsyncClient(**client_kwargs) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    cookies=options.cookies,
                    auth=auth
                )
                
                return {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content': response.content,
                    'text': response.text,
                    'size': len(response.content),
                    'response_time': time.time() - start_time,
                    'redirect_url': str(response.headers.get('location', ''))
                }
                
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Request failed for {url}: {str(e)}")
            return None
            
    def parse_response(
        self, 
        url: str, 
        path: str,
        response_data: Dict[str, Any], 
        options: ScanOptions
    ) -> Optional[ScanResult]:
        """Parse HTTP response and create ScanResult"""
        status_code = response_data['status_code']
        
        # Check if status code should be included
        # First, always exclude specified codes (typically 404)
        if status_code in options.exclude_status_codes:
            return None
            
        # Check if path is blacklisted for this status code
        if self._is_blacklisted(path, status_code, options):
            return None
        
        # Check if response is a wildcard response
        wildcard_info = self._wildcard_responses.get(url.rsplit('/', 1)[0] + '/')
        if wildcard_info and self._is_wildcard_response(response_data, wildcard_info):
            return None
            
        # If include_status_codes is specified, use it as a whitelist
        if options.include_status_codes:
            if status_code not in options.include_status_codes:
                return None
        # Otherwise, if status_codes is customized (not default), use it as whitelist
        elif options.status_codes and options.status_codes != [200, 204, 301, 302, 307, 401, 403]:
            if status_code not in options.status_codes:
                return None
        # If using defaults, include all non-excluded status codes
        # This ensures we don't miss important paths that return unusual status codes
            
        # Check size exclusions
        size = response_data['size']
        if size in options.exclude_sizes:
            return None
            
        # Check text exclusions
        text = response_data.get('text', '')
        for exclude_text in options.exclude_texts:
            if exclude_text in text:
                return None
                
        # Check regex exclusions
        if options.exclude_regex:
            if re.search(options.exclude_regex, text):
                return None
                
        # Detect if path is likely a directory
        is_directory = self._is_directory(path, response_data)
        
        result = ScanResult(
            url=url,
            path=path,
            status_code=status_code,
            size=size,
            redirect_url=response_data.get('redirect_url'),
            content_type=response_data['headers'].get('content-type'),
            response_time=response_data['response_time'],
            is_directory=is_directory
        )
        
        return result
        
    def _is_directory(self, path: str, response_data: Dict[str, Any]) -> bool:
        """Detect if a path is likely a directory"""
        # Check if path ends with /
        if path.endswith('/'):
            return True
            
        # Check for directory listing indicators
        text = response_data.get('text', '').lower()
        directory_indicators = [
            'index of',
            'directory listing',
            'parent directory',
            '<title>index of',
            '<h1>index of'
        ]
        
        if any(indicator in text for indicator in directory_indicators):
            return True
            
        # Check if response is a redirect to path with trailing slash
        redirect_url = response_data.get('redirect_url', '')
        if redirect_url and redirect_url.endswith(path + '/'):
            return True
            
        # Check content type - directories often have text/html
        content_type = response_data.get('headers', {}).get('content-type', '')
        status_code = response_data.get('status_code')
        
        # If path has no extension and returns HTML, likely a directory
        if (not any(path.endswith(ext) for ext in ['.php', '.html', '.htm', '.asp', '.aspx', '.jsp', '.txt', '.xml', '.json']) 
            and 'text/html' in content_type 
            and status_code in [200, 403]):
            return True
            
        return False
        
    def _should_include_result(
        self, 
        result: ScanResult, 
        options: ScanOptions
    ) -> bool:
        """Check if result should be included based on filters"""
        # Status code already checked in parse_response
        # Additional filtering logic can be added here
        return True
        
    async def _handle_recursive_scan(
        self,
        base_url: str,
        options: ScanOptions,
        current_depth: int = 0
    ):
        """Handle smart recursive scanning - continues until no new content found"""
        # Check depth limit (0 means unlimited)
        if options.recursion_depth > 0 and current_depth >= options.recursion_depth:
            return
            
        # Initialize tracking sets if not exists
        if not hasattr(self, '_deep_scanned_dirs'):
            self._deep_scanned_dirs = set()
        if not hasattr(self, '_deep_analyzed_endpoints'):
            self._deep_analyzed_endpoints = set()
        if not hasattr(self, '_recursive_scan_queue'):
            self._recursive_scan_queue = set()
            
        if self.logger:
            self.logger.info(f"Starting recursive scan at depth {current_depth}")
        
        # Continue scanning until no new viable paths are found
        while True:
            # Track initial result count
            initial_result_count = len(self._results)
            
            # Find all unscanned directories from ALL results (not just base_url)
            # Skip 403 directories as they are forbidden
            all_directories = []
            forbidden_directories = []
            for result in self._results:
                if result.is_directory and result.url not in self._deep_scanned_dirs:
                    if result.status_code in [200, 301, 302]:
                        all_directories.append(result)
                    elif result.status_code == 403:
                        forbidden_directories.append(result)
            
            if forbidden_directories and self.logger:
                self.logger.info(f"Skipping {len(forbidden_directories)} forbidden (403) directories")
                for forbidden in forbidden_directories[:5]:  # Show first 5
                    self.logger.debug(f"  - Skipped: {forbidden.path} (403 Forbidden)")
            
            if not all_directories:
                if self.logger:
                    self.logger.info("No new directories to scan, stopping recursion")
                break
                
            if self.logger:
                self.logger.info(f"Found {len(all_directories)} unscanned directories")
            
            # Process each unscanned directory
            for dir_result in all_directories:
                if self._stop_event.is_set():
                    break
                    
                dir_url = dir_result.url
                if not dir_url.endswith('/'):
                    dir_url += '/'
                
                # Skip if already scanned
                if dir_url in self._deep_scanned_dirs:
                    continue
                    
                self._deep_scanned_dirs.add(dir_url)
                
                if self.logger:
                    self.logger.info(f"Scanning directory: {dir_url}")
                
                # Get wordlist for recursive scanning
                wordlist = self._get_recursive_wordlist(options)
                
                # Add any extracted paths from content analysis
                if options.crawl:
                    extracted_paths = await self._deep_content_analysis(dir_url, options)
                    if extracted_paths:
                        wordlist.extend(extracted_paths)
                        if self.logger:
                            self.logger.info(f"Added {len(extracted_paths)} paths from content analysis")
                
                # Generate paths to scan
                paths = self._generate_paths(wordlist, options)
                
                # Filter out already scanned paths
                new_paths = []
                for path in paths:
                    full_path = urljoin(dir_url, path)
                    if full_path not in self._scanned_paths:
                        new_paths.append(path)
                
                if new_paths:
                    if self.logger:
                        self.logger.info(f"Scanning {len(new_paths)} new paths in {dir_url}")
                    
                    # Create new options without recursion to avoid nested recursion
                    scan_options = ScanOptions(**options.__dict__)
                    scan_options.recursive = False
                    
                    # Scan the new paths
                    await self._scan_paths(dir_url, new_paths, scan_options)
            
            # Also process files for content extraction if crawl is enabled
            if options.crawl:
                all_files = [r for r in self._results 
                            if r.status_code in [200] and 
                            not r.is_directory and 
                            r.url not in self._deep_analyzed_endpoints]
                
                for file_result in all_files[:50]:  # Limit to avoid too many requests
                    if self._stop_event.is_set():
                        break
                    
                    if file_result.url in self._deep_analyzed_endpoints:
                        continue
                        
                    self._deep_analyzed_endpoints.add(file_result.url)
                    
                    # Extract paths from file content
                    extracted_paths = await self._deep_content_analysis(file_result.url, options)
                    if extracted_paths:
                        if self.logger:
                            self.logger.info(f"Found {len(extracted_paths)} paths in {file_result.path}")
                        
                        # Determine base directory for the file
                        dir_base = '/'.join(file_result.url.split('/')[:-1]) + '/'
                        
                        # Filter and prepare new paths
                        new_paths = []
                        for path in extracted_paths:
                            full_path = urljoin(dir_base, path)
                            if full_path not in self._scanned_paths:
                                new_paths.append(path)
                        
                        if new_paths:
                            scan_options = ScanOptions(**options.__dict__)
                            scan_options.recursive = False
                            await self._scan_paths(dir_base, new_paths, scan_options)
            
            # Check if we found any new results
            new_results_count = len(self._results) - initial_result_count
            
            if new_results_count == 0:
                if self.logger:
                    self.logger.info("No new results found, stopping recursion")
                break
            else:
                if self.logger:
                    self.logger.info(f"Found {new_results_count} new results, continuing recursion...")
                current_depth += 1
                
                # Check depth limit
                if options.recursion_depth > 0 and current_depth >= options.recursion_depth:
                    if self.logger:
                        self.logger.info(f"Reached maximum recursion depth: {options.recursion_depth}")
                    break
        
        # AFTER RECURSIVE SCAN: Perform deep analysis on ALL discovered endpoints
        if options.crawl and current_depth == 0:  # Only do this at the top level
            await self._deep_analyze_all_endpoints(options)
    
    def _get_recursive_wordlist(self, options: ScanOptions) -> List[str]:
        """Get wordlist for recursive scanning - use the same wordlist as initial scan"""
        # Use the stored original wordlist for consistency
        if hasattr(self, '_original_wordlist') and self._original_wordlist:
            return self._original_wordlist
        
        # Fallback to comprehensive wordlist
        common_items = [
            # Common directories
            'admin', 'api', 'app', 'assets', 'backup', 'bin', 'cache', 'cgi-bin',
            'config', 'console', 'css', 'data', 'database', 'db', 'debug', 'demo',
            'dev', 'dist', 'doc', 'docs', 'download', 'downloads', 'error', 'errors',
            'files', 'fonts', 'home', 'images', 'img', 'include', 'includes', 'js',
            'lib', 'library', 'log', 'logs', 'mail', 'media', 'modules', 'old',
            'private', 'public', 'resources', 'scripts', 'secure', 'server', 'src',
            'static', 'storage', 'system', 'temp', 'test', 'tests', 'tmp', 'tools',
            'upload', 'uploads', 'user', 'users', 'var', 'vendor', 'views',
            
            # Additional directories often missed
            'external', 'internal', 'portal', 'files', 'share', 'common', 'global',
            'local', 'build', 'dist', 'output', 'export', 'import', 'migrations',
            
            # Common files
            'index.php', 'index.html', 'index.htm', 'default.php', 'default.html',
            'home.php', 'main.php', 'admin.php', 'login.php', 'config.php',
            'configuration.php', 'settings.php', 'info.php', 'phpinfo.php',
            'test.php', 'demo.php', 'example.php', 'sample.php',
            '.htaccess', '.htpasswd', 'robots.txt', 'sitemap.xml', '.env',
            'composer.json', 'package.json', 'README.md', 'readme.txt',
            'CHANGELOG.md', 'LICENSE', 'VERSION', 'INSTALL.md',
            
            # API versions
            'v1', 'v2', 'v3', 'api/v1', 'api/v2', 'api/v3',
            
            # CMS specific
            'wp-admin', 'wp-content', 'wp-includes', 'administrator', 'components',
            'modules', 'plugins', 'themes', 'templates',
            
            # Framework/library specific
            'vendor', 'node_modules', 'bower_components', 'packages',
            'phpids', 'phpmyadmin', 'phpMyAdmin', 'pma', 'mysql', 'sqlite',
            
            # Version numbers (common in libraries)
            '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9',
            '1.0', '1.1', '1.2', '2.0', '2.1', '3.0',
            
            # Hidden/backup files
            '.git', '.svn', '.env', '.config', '.backup', 'backup.sql', 'dump.sql',
            'database.sql', 'db_backup.sql', 'mysql.sql', 'data.sql'
        ]
        
        # If dynamic wordlist has been populated, add those too
        if hasattr(self, '_dynamic_wordlist') and self._dynamic_wordlist:
            common_items.extend(list(self._dynamic_wordlist))
        
        return common_items
            
    def filter_results(
        self, 
        results: List[ScanResult], 
        filters: Dict[str, Any]
    ) -> List[ScanResult]:
        """Filter results based on provided criteria"""
        filtered = results.copy()
        
        # Filter by status code
        if 'status_codes' in filters:
            filtered = [
                r for r in filtered 
                if r.status_code in filters['status_codes']
            ]
            
        # Filter by size
        if 'min_size' in filters:
            filtered = [
                r for r in filtered 
                if r.size >= filters['min_size']
            ]
        if 'max_size' in filters:
            filtered = [
                r for r in filtered 
                if r.size <= filters['max_size']
            ]
            
        # Filter by content type
        if 'content_types' in filters:
            filtered = [
                r for r in filtered 
                if any(ct in (r.content_type or '') for ct in filters['content_types'])
            ]
            
        # Filter by path pattern
        if 'path_pattern' in filters:
            pattern = re.compile(filters['path_pattern'])
            filtered = [
                r for r in filtered 
                if pattern.search(r.path)
            ]
            
        # Filter by response time
        if 'max_response_time' in filters:
            filtered = [
                r for r in filtered 
                if r.response_time <= filters['max_response_time']
            ]
            
        return filtered
        
    def get_scan_statistics(self) -> ScanStatistics:
        """Get current scan statistics"""
        return self._stats
        
    def stop_scan(self):
        """Stop the current scan"""
        self._stop_event.set()
        if self.logger:
            self.logger.info("Scan stop requested")
        
    def export_results(self, format: str = 'json') -> str:
        """Export results in various formats for MCP coordinator"""
        if format == 'json':
            import json
            return json.dumps([
                {
                    'url': r.url,
                    'path': r.path,
                    'status_code': r.status_code,
                    'size': r.size,
                    'content_type': r.content_type,
                    'response_time': r.response_time,
                    'is_directory': r.is_directory,
                    'timestamp': r.timestamp
                }
                for r in self._results
            ], indent=2)
        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=['url', 'path', 'status_code', 'size', 'content_type', 'response_time']
            )
            writer.writeheader()
            for r in self._results:
                writer.writerow({
                    'url': r.url,
                    'path': r.path,
                    'status_code': r.status_code,
                    'size': r.size,
                    'content_type': r.content_type,
                    'response_time': r.response_time
                })
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
            
    def get_results(self) -> List[ScanResult]:
        """Get current results"""
        with self._lock:
            return self._results.copy()
            
    def clear_results(self):
        """Clear current results"""
        with self._lock:
            self._results.clear()
            self._scanned_paths.clear()
            self._discovered_important_paths.clear()
            self._dynamic_wordlist.clear()
            self._deep_scanned_dirs.clear()
            self._deep_analyzed_endpoints.clear()
            self._recursive_scan_queue.clear()
    
    def _analyze_and_expand(self, result: ScanResult):
        """Analyze discovered path and expand wordlist intelligently"""
        # Get expansion keywords based on discovered path
        keywords = self.intelligent_scanner.get_expansion_keywords(result.path)
        
        # Add to dynamic wordlist
        self._dynamic_wordlist.update(keywords)
        
        # Check if this is an important path
        rules = self.intelligent_scanner.analyze_path(result.path, result.status_code)
        if rules and rules[0][1].priority >= 70:
            self._discovered_important_paths.append({
                'path': result.path,
                'status': result.status_code,
                'rules': [(name, rule.priority) for name, rule in rules],
                'timestamp': time.time()
            })
            
            if self.logger:
                self.logger.info(f"Important path discovered: {result.path} (Priority: {rules[0][1].priority})")
    
    def get_intelligent_wordlist(self, base_wordlist: List[str], context: Optional[Dict] = None) -> List[str]:
        """Generate intelligent wordlist based on discoveries and context"""
        wordlist = set(base_wordlist)
        
        # Add dynamic discoveries
        wordlist.update(self._dynamic_wordlist)
        
        # Add context-aware keywords
        if context:
            smart_words = self.intelligent_scanner.generate_smart_wordlist(context)
            wordlist.update(smart_words)
        
        # Prioritize important keywords
        priority_words = []
        regular_words = []
        
        for word in wordlist:
            # Check if word matches high-priority patterns
            is_priority = False
            for rule_name, rule in self.intelligent_scanner.rules.items():
                if rule.priority >= 80 and any(kw in word for kw in rule.keywords[:5]):
                    is_priority = True
                    break
            
            if is_priority:
                priority_words.append(word)
            else:
                regular_words.append(word)
        
        # Return prioritized list
        return priority_words + regular_words
    
    def get_scan_insights(self) -> Dict[str, Any]:
        """Get intelligent insights from the scan"""
        insights = {
            'important_paths': self._discovered_important_paths,
            'discovered_patterns': [],
            'recommendations': [],
            'risk_assessment': {},
            'technology_hints': set()
        }
        
        # Analyze patterns
        path_patterns = defaultdict(int)
        for result in self._results:
            if result.status_code in [200, 301, 302, 403]:
                # Extract patterns
                if '/admin' in result.path:
                    path_patterns['admin'] += 1
                if '/api' in result.path:
                    path_patterns['api'] += 1
                if '.git' in result.path:
                    path_patterns['vcs'] += 1
                if 'backup' in result.path or '.bak' in result.path:
                    path_patterns['backup'] += 1
                if '/wp-' in result.path:
                    insights['technology_hints'].add('WordPress')
                if '/vendor/' in result.path:
                    insights['technology_hints'].add('PHP/Composer')
                if '/node_modules/' in result.path:
                    insights['technology_hints'].add('Node.js')
        
        insights['discovered_patterns'] = dict(path_patterns)
        
        # Risk assessment
        risk_score = 0
        risks = []
        
        if path_patterns.get('admin', 0) > 0:
            risk_score += 30
            risks.append("Administrative interfaces exposed")
        
        if path_patterns.get('vcs', 0) > 0:
            risk_score += 40
            risks.append("Version control files accessible")
        
        if path_patterns.get('backup', 0) > 0:
            risk_score += 35
            risks.append("Backup files found")
        
        if path_patterns.get('api', 0) > 0:
            risk_score += 20
            risks.append("API endpoints discovered")
        
        insights['risk_assessment'] = {
            'score': min(risk_score, 100),
            'level': 'High' if risk_score >= 70 else 'Medium' if risk_score >= 40 else 'Low',
            'risks': risks
        }
        
        # Recommendations
        if path_patterns.get('admin', 0) > 0:
            insights['recommendations'].append("Deep scan administrative interfaces with authentication wordlists")
        
        if path_patterns.get('api', 0) > 0:
            insights['recommendations'].append("Test API endpoints for authentication bypass and information disclosure")
        
        if path_patterns.get('vcs', 0) > 0:
            insights['recommendations'].append("Extract source code from version control files")
        
        if path_patterns.get('backup', 0) > 0:
            insights['recommendations'].append("Download and analyze backup files for sensitive data")
        
        # Convert set to list for JSON serialization
        insights['technology_hints'] = list(insights['technology_hints'])
        
        return insights
    
    async def execute_scan(self, scan_request: ScanRequest) -> ScanResponse:
        """Execute a scan based on ScanRequest and return ScanResponse"""
        from datetime import datetime
        
        start_time = datetime.now()
        
        try:
            # Load wordlists (supports multiple wordlists)
            wordlist_paths = self._load_wordlists(scan_request)
            
            # Create scan options from request
            options = ScanOptions(
                extensions=scan_request.extensions,
                threads=scan_request.threads,
                timeout=scan_request.timeout,
                delay=scan_request.delay,
                user_agent=scan_request.user_agent,
                follow_redirects=scan_request.follow_redirects,
                headers=scan_request.custom_headers,
                proxy=scan_request.proxy,
                max_retries=scan_request.max_retries,
                exclude_status_codes=[int(x.strip()) for x in scan_request.exclude_status.split(',')] if scan_request.exclude_status else [404],
                include_status_codes=[int(x.strip()) for x in scan_request.include_status.split(',')] if scan_request.include_status else None,
                recursive=scan_request.recursive,
                recursion_depth=scan_request.recursion_depth,
                debug_enabled=scan_request.debug_enabled,
                debug_live_display=scan_request.debug_live_display,
                debug_export_path=scan_request.debug_export_path
            )
            
            # Execute scan
            await self.scan_target(
                scan_request.base_url,  # url (positional)
                wordlist_paths,         # wordlist (positional)
                options                 # options (positional)
            )
        except asyncio.CancelledError:
            if self.logger:
                self.logger.info("Scan cancelled by user")
            self.stop_scan()
            raise
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Convert results to response format
        results = []
        for result in self._results:
            results.append({
                'path': result.path,
                'url': result.url,
                'status': result.status_code,
                'size': result.size,
                'content_type': result.content_type,
                'response_time': result.response_time,
                'redirect': result.redirect_url,
                'is_directory': result.is_directory
            })
        
        # Build statistics
        statistics = {
            'total_requests': self._stats.total_requests,
            'found_paths': len(self._results),
            'errors': len(self._stats.errors),
            'filtered': self._stats.filtered_results,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration': duration,
            'requests_per_second': self._stats.requests_per_second
        }
        
        return ScanResponse(
            target_url=scan_request.base_url,
            results=results,
            statistics=statistics,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration=duration
        )
    
    def _load_wordlist(self, wordlist_path: str) -> List[str]:
        """Load wordlist from file or use as direct input"""
        if isinstance(wordlist_path, list):
            return wordlist_path
        
        # Check if it's a file path
        wordlist_file = Path(wordlist_path)
        if self.logger:
            self.logger.debug(f"Loading wordlist: {wordlist_path}, absolute: {wordlist_file.is_absolute()}")
        
        if not wordlist_file.is_absolute():
            # Try to find in wordlists directory
            if self.settings and hasattr(self.settings, 'paths') and 'wordlists' in self.settings.paths:
                # Handle nested wordlists path structure
                wordlists_path = self.settings.paths['wordlists']
                if isinstance(wordlists_path, dict):
                    # Try different locations in order
                    wordlists_base = wordlists_path.get('base', wordlists_path.get('general', 'wordlists'))
                else:
                    wordlists_base = wordlists_path
                
                # Remove 'wordlists/' prefix if present to avoid duplication
                clean_path = wordlist_path.replace('wordlists/', '')
                wordlist_file = Path(wordlists_base) / clean_path
                if self.logger:
                    self.logger.debug(f"Resolved to: {wordlist_file}")
        
        if wordlist_file.exists():
            with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                if self.logger:
                    self.logger.debug(f"Loaded {len(lines)} lines from {wordlist_file}")
                return lines
        else:
            if self.logger:
                self.logger.warning(f"Wordlist file not found: {wordlist_file}, treating as comma-separated list")
            # Treat as comma-separated list
            return [w.strip() for w in wordlist_path.split(',') if w.strip()]
    
    def _load_wordlists(self, scan_request: ScanRequest) -> List[str]:
        """Load and combine multiple wordlists based on scan request"""
        all_words = set()
        
        # Debug logging
        if self.logger:
            self.logger.debug(f"Loading wordlists - wordlist: {scan_request.wordlist}, wordlist_type: {scan_request.wordlist_type}")
            self.logger.debug(f"Config wordlists: {self.config.get('wordlists', {})}")
        
        # Determine which wordlist to use based on wordlist_type
        primary_wordlist = None
        if scan_request.wordlist_type in self.config.get('wordlists', {}):
            primary_wordlist = self.config['wordlists'][scan_request.wordlist_type]
        elif scan_request.wordlist:
            primary_wordlist = scan_request.wordlist
        else:
            primary_wordlist = self.config.get('default_wordlist', 'wordlists/combined-enhanced.txt')
        
        # Load primary wordlist
        if primary_wordlist:
            words = self._load_wordlist(primary_wordlist)
            all_words.update(words)
            if self.logger:
                self.logger.info(f"Loaded {len(words)} words from primary wordlist: {primary_wordlist}")
        
        # Load additional wordlists
        for wordlist in scan_request.additional_wordlists:
            words = self._load_wordlist(wordlist)
            all_words.update(words)
            if self.logger:
                self.logger.info(f"Loaded {len(words)} words from additional wordlist: {wordlist}")
        
        # Convert to sorted list for consistent ordering
        return sorted(list(all_words))
    
    # Enhanced features from original dirsearch
    
    def _load_blacklists(self) -> Dict[int, List[str]]:
        """Load blacklist files for status codes"""
        blacklists = {}
        blacklist_dir = Path("wordlists") / "blacklists"
        
        for status in [400, 403, 500]:
            blacklist_file = blacklist_dir / f"{status}_blacklist.txt"
            if blacklist_file.exists():
                try:
                    with open(blacklist_file, 'r') as f:
                        blacklists[status] = [line.strip() for line in f if line.strip()]
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Failed to load blacklist for {status}: {e}")
        
        return blacklists
    
    def _get_filter_reason(self, result: ScanResult, options: ScanOptions) -> str:
        """Get the reason why a result was filtered"""
        if result.status_code in options.exclude_status_codes:
            return f"Excluded status code: {result.status_code}"
        elif options.include_status_codes and result.status_code not in options.include_status_codes:
            return f"Not in included status codes: {result.status_code}"
        elif hasattr(self, '_wildcard_responses'):
            wildcard_info = self._wildcard_responses.get(result.url.rsplit('/', 1)[0] + '/')
            if wildcard_info and result.status_code in wildcard_info:
                return f"Wildcard response detected for status {result.status_code}"
        elif self._is_blacklisted(result.path, result.status_code, options):
            return "Blacklisted path pattern"
        else:
            return "Unknown filter reason"
    
    def _load_user_agents(self) -> List[str]:
        """Load user agents from file"""
        ua_file = Path("wordlists") / "user-agents.txt"
        if ua_file.exists():
            try:
                with open(ua_file, 'r') as f:
                    return [line.strip() for line in f if line.strip()]
            except Exception:
                pass
        
        # Default user agents
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
    
    def _get_random_user_agent(self) -> str:
        """Get random user agent"""
        if not self._user_agents:
            self._user_agents = self._load_user_agents()
        return random.choice(self._user_agents)
    
    async def _detect_wildcard(self, base_url: str, options: ScanOptions) -> Optional[Dict[str, Any]]:
        """Detect wildcard responses"""
        if not options.detect_wildcards:
            return None
        
        # Generate random paths for wildcard detection
        random_paths = []
        for _ in range(3):  # Test with 3 random paths for better accuracy
            random_path = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            random_paths.append(random_path)
        
        responses = []
        status_codes = set()
        sizes = set()
        
        for path in random_paths:
            try:
                response_data = await self._make_request(urljoin(base_url, path), options)
                if response_data:
                    responses.append(response_data)
                    status_codes.add(response_data['status_code'])
                    sizes.add(response_data['size'])
            except Exception:
                pass
        
        wildcard_info = {}
        
        # Check for 403 wildcard pattern
        if len(responses) >= 2 and all(r['status_code'] == 403 for r in responses):
            # All random paths return 403 - likely wildcard
            if len(sizes) == 1:  # All same size
                if self.logger:
                    self.logger.warning(f"Detected 403 wildcard: all random paths return 403 with same size")
                
                wildcard_info[403] = {
                    'detected': True,
                    'size': list(sizes)[0],
                    'parser': None
                }
        
        # Check for content-based wildcard pattern
        if len(responses) >= 2:
            # Group by status code
            status_groups = {}
            for resp in responses:
                status = resp['status_code']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(resp)
            
            # Check each status code group
            for status, resp_list in status_groups.items():
                if len(resp_list) >= 2:
                    content1 = resp_list[0].get('text', '')
                    content2 = resp_list[1].get('text', '')
                    
                    if content1 and content2:
                        parser = DynamicContentParser(content1, content2)
                        wildcard_info[status] = {
                            'detected': True,
                            'parser': parser,
                            'size': resp_list[0]['size']
                        }
        
        return wildcard_info if wildcard_info else None
    
    def _is_wildcard_response(self, response_data: Dict[str, Any], wildcard_info: Dict[str, Any]) -> bool:
        """Check if response matches wildcard pattern"""
        if not wildcard_info:
            return False
        
        status_code = response_data['status_code']
        
        # Check if we have wildcard info for this status code
        if status_code not in wildcard_info:
            return False
        
        wc_data = wildcard_info[status_code]
        if not wc_data.get('detected'):
            return False
        
        # For 403 wildcards, check size matching
        if status_code == 403 and 'size' in wc_data:
            # If size matches wildcard size, it's likely a false positive
            if response_data['size'] == wc_data['size']:
                if self.logger:
                    self.logger.debug(f"Filtering 403 wildcard response: {response_data.get('path')} (size: {response_data['size']})")
                return True
        
        # Check content similarity with parser
        parser = wc_data.get('parser')
        if parser:
            content = response_data.get('text', '')
            return parser.compare_to(content)
        
        return False
    
    def _is_blacklisted(self, path: str, status_code: int, options: ScanOptions) -> bool:
        """Check if path is blacklisted for status code"""
        blacklist = options.blacklists.get(status_code, [])
        if not blacklist:
            blacklist = self._blacklists.get(status_code, [])
        
        for pattern in blacklist:
            if pattern in path:
                return True
        
        return False
    
    async def _crawl_response(self, response_data: Dict[str, Any], base_url: str) -> List[str]:
        """Crawl response to find new paths"""
        if not BeautifulSoup:
            return []
        
        content_type = response_data.get('headers', {}).get('content-type', '')
        content = response_data.get('text', '')
        
        if not content:
            return []
        
        discovered_paths = set()
        
        # HTML crawling
        if 'text/html' in content_type:
            try:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract from common attributes
                for tag in ['a', 'script', 'link', 'img', 'form']:
                    for element in soup.find_all(tag):
                        for attr in ['href', 'src', 'action']:
                            value = element.get(attr)
                            if value:
                                # Clean and normalize path
                                path = self._normalize_crawled_path(value, base_url)
                                if path:
                                    discovered_paths.add(path)
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"HTML parsing error: {e}")
        
        # robots.txt parsing
        elif response_data.get('path') == 'robots.txt':
            for line in content.split('\n'):
                if line.startswith(('Allow:', 'Disallow:')):
                    path = line.split(':', 1)[1].strip()
                    if path and path != '/':
                        discovered_paths.add(path.lstrip('/'))
        
        # General text crawling for URLs
        else:
            # Find URLs in text
            url_pattern = re.compile(r'(?:href|src|action)=["\']?([^"\'>\s]+)')
            for match in url_pattern.findall(content):
                path = self._normalize_crawled_path(match, base_url)
                if path:
                    discovered_paths.add(path)
        
        # Advanced endpoint extraction using regex patterns
        endpoint_patterns = [
            # API endpoints
            r'/api/[a-zA-Z0-9_\-/]+',
            r'/v[0-9]+/[a-zA-Z0-9_\-/]+',
            # PHP files
            r'/[a-zA-Z0-9_\-]+\.php',
            # Common paths
            r'/[a-zA-Z]+/[a-zA-Z0-9_\-]+',
            # JavaScript paths
            r'["\'](/[a-zA-Z0-9_\-/.]+)["\']',
            # URL in comments
            r'<!--.*?(/[a-zA-Z0-9_\-/.]+).*?-->',
        ]
        
        for pattern in endpoint_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, str) and match.startswith('/'):
                    path = self._normalize_crawled_path(match, base_url)
                    if path:
                        discovered_paths.add(path)
        
        return list(discovered_paths)
    
    async def _deep_content_analysis(self, url: str, options: ScanOptions) -> List[str]:
        """Perform deep content analysis to extract endpoints using multiple techniques"""
        extracted_paths = set()
        
        try:
            # Get the response
            response = await self._make_request(url, options)
            if not response or 'text' not in response:
                return []
                
            content = response['text']
            content_type = response.get('headers', {}).get('content-type', '')
            
            # 1. Enhanced regex patterns for endpoint extraction
            endpoint_patterns = [
                # API endpoints
                r'/api/v?\d*/[a-zA-Z0-9_\-/]+',
                r'/v\d+/[a-zA-Z0-9_\-/]+',
                r'/graphql[a-zA-Z0-9_\-/]*',
                r'/rest/[a-zA-Z0-9_\-/]+',
                
                # File paths
                r'/[a-zA-Z0-9_\-]+\.(?:php|asp|aspx|jsp|do|action|html|htm|js|json|xml)',
                r'/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+\.(?:php|asp|aspx|jsp|do|action)',
                
                # Directory paths
                r'/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+/?',
                r'/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+/?',
                
                # URLs in JavaScript
                r'["\'](/[a-zA-Z0-9_\-/.]+)["\']',
                r'url\s*\(\s*["\']?(/[^"\')\s]+)',
                r'(?:href|src|action|data-url|data-src)\s*=\s*["\']([^"\']+)["\']',
                
                # AJAX/Fetch endpoints
                r'fetch\s*\(\s*["\']([^"\']+)["\']',
                r'\.ajax\s*\(\s*{\s*url\s*:\s*["\']([^"\']+)["\']',
                r'XMLHttpRequest.*?open\s*\(\s*["\'][A-Z]+["\']\s*,\s*["\']([^"\']+)["\']',
                
                # Form actions
                r'<form[^>]+action\s*=\s*["\']([^"\']+)["\']',
                
                # Comments might contain endpoints
                r'<!--.*?(/[a-zA-Z0-9_\-/.]+).*?-->',
                r'/\*.*?(/[a-zA-Z0-9_\-/.]+).*?\*/',
                
                # Configuration patterns
                r'(?:baseurl|base_url|apiurl|api_url|endpoint)\s*[:=]\s*["\']([^"\']+)["\']',
                
                # Import/Include statements
                r'(?:import|include|require)(?:_once)?\s*\(?["\']([^"\']+)["\']',
            ]
            
            # Extract using all patterns
            for pattern in endpoint_patterns:
                try:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        if isinstance(match, str) and match.startswith('/'):
                            # Clean and normalize the path
                            clean_path = match.strip()
                            # Remove query strings and fragments
                            clean_path = clean_path.split('?')[0].split('#')[0]
                            if clean_path and clean_path != '/':
                                extracted_paths.add(clean_path.lstrip('/'))
                except:
                    continue
            
            # 2. Parse JavaScript for dynamic endpoints
            if 'javascript' in content_type or '.js' in url:
                js_patterns = [
                    r'["\']([a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)+)["\']',
                    r'endpoint\s*:\s*["\']([^"\']+)["\']',
                    r'route\s*:\s*["\']([^"\']+)["\']',
                ]
                for pattern in js_patterns:
                    try:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if '/' in match and not match.startswith('http'):
                                extracted_paths.add(match.lstrip('/'))
                    except:
                        continue
            
            # 3. Look for hidden/debug endpoints
            debug_patterns = [
                r'(?:debug|test|dev|staging)[_\-]?(?:url|endpoint|api).*?["\']([^"\']+)["\']',
                r'/(?:debug|test|dev|admin|backup|old|temp|tmp)/[a-zA-Z0-9_\-]+',
            ]
            for pattern in debug_patterns:
                try:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('/'):
                            extracted_paths.add(match.lstrip('/'))
                except:
                    continue
            
            # 4. Extract from meta tags and headers
            meta_patterns = [
                r'<meta[^>]+content\s*=\s*["\']([^"\']+)["\'][^>]*>',
                r'<link[^>]+href\s*=\s*["\']([^"\']+)["\'][^>]*>',
            ]
            for pattern in meta_patterns:
                try:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if match.startswith('/') and not match.endswith('.css'):
                            extracted_paths.add(match.lstrip('/'))
                except:
                    continue
            
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Deep content analysis error: {e}")
        
        # Filter out common static assets
        filtered_paths = []
        static_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.ico', '.css', '.woff', '.woff2', '.ttf', '.svg']
        
        for path in extracted_paths:
            # Skip static assets
            if any(path.lower().endswith(ext) for ext in static_extensions):
                continue
            # Skip too long paths (likely false positives)
            if len(path) > 100:
                continue
            # Skip paths with too many special characters
            if len(re.findall(r'[^a-zA-Z0-9_\-/.]', path)) > 5:
                continue
            
            filtered_paths.append(path)
        
        return filtered_paths
    
    def _normalize_crawled_path(self, path: str, base_url: str) -> Optional[str]:
        """Normalize crawled path"""
        if not path or path.startswith(('#', 'javascript:', 'mailto:')):
            return None
        
        # Skip external URLs
        if path.startswith(('http://', 'https://')):
            parsed = urlparse(path)
            base_parsed = urlparse(base_url)
            if parsed.netloc != base_parsed.netloc:
                return None
            path = parsed.path
        
        # Remove query strings and fragments
        path = path.split('?')[0].split('#')[0]
        
        # Normalize path
        if path.startswith('/'):
            path = path[1:]
        
        # Skip media files
        media_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.css', '.js')
        if path.endswith(media_extensions):
            return None
        
        return path
    
    def _get_auth_handler(self, auth_type: str, credentials: Tuple[str, str]):
        """Get authentication handler based on type"""
        username, password = credentials
        
        if auth_type == "digest":
            return DigestAuth(username, password)
        elif auth_type == "ntlm" and NTLMAuth:
            return NTLMAuth(username, password)
        else:  # basic
            return httpx.BasicAuth(username, password)
    
    def _replace_extension_tag(self, word: str, extension: str, tag: str = "%EXT%") -> str:
        """Replace extension tag in wordlist entry"""
        return word.replace(tag, extension)
    
    def _enhance_wordlist_with_extensions(self, wordlist: List[str], extensions: List[str], tag: str = "%EXT%") -> List[str]:
        """Enhance wordlist with extension tag replacement"""
        enhanced = []
        
        for word in wordlist:
            if tag in word:
                # Replace tag with each extension
                for ext in extensions:
                    enhanced.append(self._replace_extension_tag(word, ext, tag))
            else:
                enhanced.append(word)
        
        return enhanced
    
    async def _deep_analyze_all_endpoints(self, options: ScanOptions):
        """Perform deep content analysis on ALL discovered endpoints after recursive scan"""
        if self.logger:
            self.logger.info("Starting deep analysis of all discovered endpoints...")
            
        # Log deep analysis start with debug monitor
        if self.debug_integration:
            self.debug_integration.log_recursion("[deep_analysis]", 0, starting=True)
        
        # Get all successful endpoints (200, 301, 302) - excluding 403
        endpoints_to_analyze = [
            r for r in self._results 
            if r.status_code in [200, 301, 302] and r.url not in self._deep_analyzed_endpoints
        ]
        
        if not endpoints_to_analyze:
            if self.logger:
                self.logger.info("No new endpoints to analyze")
            return
        
        if self.logger:
            self.logger.info(f"Analyzing {len(endpoints_to_analyze)} endpoints for hidden content...")
        
        # Track all extracted paths
        all_extracted_paths = set()
        endpoint_analysis_results = []
        
        # Analyze each endpoint
        for endpoint in endpoints_to_analyze:
            if self._stop_event.is_set():
                break
            
            # Skip if already analyzed
            if endpoint.url in self._deep_analyzed_endpoints:
                continue
            
            self._deep_analyzed_endpoints.add(endpoint.url)
            
            # Perform deep content analysis
            extracted_paths = await self._deep_content_analysis(endpoint.url, options)
            
            if extracted_paths:
                # Store analysis results
                endpoint_analysis_results.append({
                    'endpoint': endpoint.url,
                    'path': endpoint.path,
                    'extracted_count': len(extracted_paths),
                    'extracted_paths': extracted_paths[:10]  # Store first 10 for display
                })
                
                all_extracted_paths.update(extracted_paths)
                
                if self.logger:
                    self.logger.info(f"Extracted {len(extracted_paths)} paths from {endpoint.path}")
        
        # Store analysis results for reporting
        if not hasattr(self, '_endpoint_analysis_results'):
            self._endpoint_analysis_results = []
        self._endpoint_analysis_results.extend(endpoint_analysis_results)
        
        # Now scan all newly discovered paths
        if all_extracted_paths:
            if self.logger:
                self.logger.info(f"Total unique paths extracted: {len(all_extracted_paths)}")
            
            # Group paths by their base directory
            paths_by_dir = defaultdict(list)
            for path in all_extracted_paths:
                # Determine base directory
                if '/' in path:
                    base_dir = '/'.join(path.split('/')[:-1]) + '/'
                else:
                    base_dir = '/'
                
                # Check if path was already scanned
                full_url = urljoin(self._results[0].url.rsplit('/', 1)[0] + '/', path)
                if full_url not in self._scanned_paths:
                    paths_by_dir[base_dir].append(path.split('/')[-1])
            
            # Scan the extracted paths
            for base_dir, paths in paths_by_dir.items():
                if paths:
                    base_url = urljoin(self._results[0].url.rsplit('/', 1)[0] + '/', base_dir)
                    
                    if self.logger:
                        self.logger.info(f"Scanning {len(paths)} extracted paths in {base_dir}")
                    
                    scan_options = ScanOptions(**options.__dict__)
                    scan_options.recursive = False  # Don't recurse on these
                    scan_options.crawl = False  # Don't analyze again
                    
                    await self._scan_paths(base_url, paths, scan_options)
        
        if self.logger:
            self.logger.info("Deep endpoint analysis completed")
            
        # Log deep analysis end with debug monitor
        if self.debug_integration:
            self.debug_integration.log_recursion("[deep_analysis]", 0, starting=False)
    
    def build_directory_tree(self, results: List[ScanResult] = None) -> Dict[str, Any]:
        """Build a directory tree structure from scan results"""
        if results is None:
            results = self._results
        
        # Create tree structure
        tree = {
            'name': '/',
            'type': 'directory',
            'children': {},
            'files': []
        }
        
        for result in results:
            if result.status_code in [200, 301, 302, 403]:  # Include accessible paths
                path = result.path.strip('/')
                parts = path.split('/')
                current = tree
                
                # Navigate/create directory structure
                for i, part in enumerate(parts[:-1]):
                    if part not in current['children']:
                        current['children'][part] = {
                            'name': part,
                            'type': 'directory',
                            'children': {},
                            'files': [],
                            'status': result.status_code if i == len(parts) - 2 else None
                        }
                    current = current['children'][part]
                
                # Add the final part
                if parts:
                    final_part = parts[-1]
                    if result.is_directory or path.endswith('/'):
                        # It's a directory
                        if final_part not in current['children']:
                            current['children'][final_part] = {
                                'name': final_part,
                                'type': 'directory',
                                'children': {},
                                'files': [],
                                'status': result.status_code
                            }
                    else:
                        # It's a file
                        current['files'].append({
                            'name': final_part,
                            'type': 'file',
                            'status': result.status_code,
                            'size': result.size
                        })
        
        return tree
    
    def print_directory_tree(self, tree: Dict[str, Any] = None, prefix: str = "", is_last: bool = True) -> str:
        """Convert directory tree to string representation"""
        if tree is None:
            tree = self.build_directory_tree()
        
        output = []
        
        # Skip root node in display
        if tree['name'] != '/':
            connector = "└── " if is_last else "├── "
            status_text = f" [{tree.get('status', '')}]" if tree.get('status') else ""
            
            if tree['type'] == 'directory':
                output.append(f"{prefix}{connector}📁 {tree['name']}/{status_text}")
            else:
                output.append(f"{prefix}{connector}📄 {tree['name']}{status_text}")
            
            prefix += "    " if is_last else "│   "
        
        # Process children directories first
        children = list(tree.get('children', {}).values())
        for i, child in enumerate(children):
            is_last_child = (i == len(children) - 1) and not tree.get('files', [])
            output.extend(self.print_directory_tree(child, prefix, is_last_child).split('\n'))
        
        # Then process files
        files = tree.get('files', [])
        for i, file in enumerate(files):
            is_last_file = (i == len(files) - 1)
            connector = "└── " if is_last_file else "├── "
            status_text = f" [{file.get('status', '')}]" if file.get('status') else ""
            output.append(f"{prefix}{connector}📄 {file['name']}{status_text}")
        
        return '\n'.join(filter(None, output))
    
    def get_directory_statistics(self, results: List[ScanResult] = None) -> Dict[str, Any]:
        """Get statistics about discovered directory structure"""
        if results is None:
            results = self._results
        
        stats = {
            'total_paths': len(results),
            'directories': 0,
            'files': 0,
            'by_status': {},
            'by_depth': {},
            'largest_files': [],
            'deepest_path': '',
            'max_depth': 0
        }
        
        for result in results:
            # Count by type
            if result.is_directory:
                stats['directories'] += 1
            else:
                stats['files'] += 1
            
            # Count by status
            status = result.status_code
            if status not in stats['by_status']:
                stats['by_status'][status] = 0
            stats['by_status'][status] += 1
            
            # Count by depth
            depth = result.path.count('/')
            if result.path.endswith('/'):
                depth -= 1
            
            if depth not in stats['by_depth']:
                stats['by_depth'][depth] = 0
            stats['by_depth'][depth] += 1
            
            # Track deepest path
            if depth > stats['max_depth']:
                stats['max_depth'] = depth
                stats['deepest_path'] = result.path
            
            # Track largest files
            if not result.is_directory and result.size > 0:
                stats['largest_files'].append({
                    'path': result.path,
                    'size': result.size
                })
        
        # Sort largest files
        stats['largest_files'].sort(key=lambda x: x['size'], reverse=True)
        stats['largest_files'] = stats['largest_files'][:10]  # Keep top 10
        
        return stats