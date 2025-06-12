import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import time
import re
from pathlib import Path
from collections import defaultdict
import queue

import httpx
import aiohttp
from httpx import AsyncClient, Response as HttpxResponse
from aiohttp import ClientSession, ClientResponse


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
    proxy: Optional[str] = None
    auth: Optional[Tuple[str, str]] = None
    follow_redirects: bool = False
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
    follow_redirects: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None
    max_retries: int = 3
    exclude_status: Optional[str] = "404"
    include_status: Optional[str] = None
    recursive: bool = True  # Default to True for recursive scanning
    recursion_depth: int = 3  # Default depth of 3 levels


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
        
        # Default configuration
        self.config = settings.default_scan_config if settings else {
            'threads': 10,
            'timeout': 10,
            'user_agent': 'Mozilla/5.0 (compatible; Dirsearch-MCP/1.0)',
            'follow_redirects': True,
            'exclude_status': '404'
        }
        
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
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
        options: Optional[ScanOptions] = None
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
            
        # Reset state
        self._stats = ScanStatistics()
        self._results.clear()
        self._scanned_paths.clear()
        self._stop_event.clear()
        
        # Prepare URL
        url = url.rstrip('/')
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        # Generate paths to scan
        paths = self._generate_paths(wordlist, options)
        
        # Start scanning
        if self.logger:
            self.logger.info(f"Starting scan on {url} with {len(paths)} paths")
            
        await self._scan_paths(url, paths, options)
        
        self._stats.end_time = time.time()
        
        return self._results
        
    def _generate_paths(self, wordlist: List[str], options: ScanOptions) -> List[str]:
        """Generate all path combinations based on wordlist and options"""
        paths = set()
        
        for word in wordlist:
            # Handle subdirectories
            for subdir in options.subdirs or ['']:
                base_path = f"{subdir}/{word}" if subdir else word
                
                # Handle prefixes and suffixes
                for prefix in options.prefixes:
                    for suffix in options.suffixes:
                        path = f"{prefix}{base_path}{suffix}"
                        
                        # Handle extensions
                        if options.extensions:
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
                
            task = self._scan_single_path(
                base_url, path, options, semaphore, i, len(paths)
            )
            tasks.append(task)
            
            # Add delay if specified
            if options.delay > 0:
                await asyncio.sleep(options.delay)
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
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
            # Skip if already scanned
            with self._lock:
                if path in self._scanned_paths:
                    return None
                self._scanned_paths.add(path)
                
            url = urljoin(base_url, path)
            
            # Update progress
            if self._progress_callback:
                self._progress_callback(current + 1, total)
                
            # Perform request with retries
            for attempt in range(options.max_retries):
                try:
                    response_data = await self._make_request(url, options)
                    if response_data:
                        result = self.parse_response(url, path, response_data, options)
                        
                        if result and self._should_include_result(result, options):
                            with self._lock:
                                self._results.append(result)
                                self._stats.successful_requests += 1
                                
                            if self._result_callback:
                                self._result_callback(result)
                                
                            return result
                        else:
                            with self._lock:
                                self._stats.filtered_results += 1
                                
                    break
                    
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
        headers = {
            'User-Agent': options.user_agent,
            **options.headers
        }
        
        auth = httpx.BasicAuth(*options.auth) if options.auth else None
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(
                timeout=options.timeout,
                follow_redirects=options.follow_redirects,
                proxies=options.proxy,
                verify=False
            ) as client:
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
                
        except Exception:
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
        if options.include_status_codes:
            if status_code not in options.include_status_codes:
                return None
        elif status_code in options.exclude_status_codes:
            return None
        elif status_code not in options.status_codes:
            return None
            
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
            '<title>index of'
        ]
        
        return any(indicator in text for indicator in directory_indicators)
        
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
        """Handle recursive scanning of discovered directories"""
        if current_depth >= options.recursion_depth:
            return
            
        # Find directories from results
        directories = [
            r for r in self._results 
            if r.is_directory and r.status_code in [200, 301, 302, 403]
        ]
        
        if not directories:
            return
            
        if self.logger:
            self.logger.info(f"Found {len(directories)} directories for recursive scan at depth {current_depth + 1}")
        
        # Scan each directory
        for dir_result in directories:
            if self._stop_event.is_set():
                break
                
            # Ensure the path ends with /
            dir_path = dir_result.path
            if not dir_path.endswith('/'):
                dir_path += '/'
                
            new_base_url = urljoin(base_url, dir_path)
            
            if self.logger:
                self.logger.info(f"Recursive scan: {new_base_url} (depth: {current_depth + 1})")
            
            # Generate paths for this subdirectory
            wordlist = self._get_recursive_wordlist(options)
            paths = self._generate_paths(wordlist, options)
            
            # Filter out already scanned paths
            new_paths = []
            for path in paths:
                full_path = urljoin(new_base_url, path)
                if full_path not in self._scanned_paths:
                    new_paths.append(path)
            
            if new_paths:
                # Scan the subdirectory
                await self._scan_paths(new_base_url, new_paths, options)
                
                # Recursively scan any new directories found
                if current_depth + 1 < options.recursion_depth:
                    await self._handle_recursive_scan(new_base_url, options, current_depth + 1)
    
    def _get_recursive_wordlist(self, options: ScanOptions) -> List[str]:
        """Get wordlist for recursive scanning (can be different from initial scan)"""
        # For recursive scans, we might want to use a smaller wordlist
        # This is a simplified version - you could load a specific recursive wordlist
        common_dirs = [
            'admin', 'api', 'backup', 'config', 'data', 'db', 'files', 
            'images', 'includes', 'js', 'lib', 'logs', 'media', 'scripts',
            'src', 'static', 'temp', 'test', 'tmp', 'upload', 'uploads',
            'user', 'users', 'vendor', 'wp-admin', 'wp-content', 'wp-includes'
        ]
        return common_dirs
            
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
    
    async def execute_scan(self, scan_request: ScanRequest) -> ScanResponse:
        """Execute a scan based on ScanRequest and return ScanResponse"""
        from datetime import datetime
        
        start_time = datetime.now()
        
        # Load wordlist
        wordlist_paths = self._load_wordlist(scan_request.wordlist)
        
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
            recursion_depth=scan_request.recursion_depth
        )
        
        # Execute scan
        await self.scan_target(
            scan_request.base_url,  # url (positional)
            wordlist_paths,         # wordlist (positional)
            options                 # options (positional)
        )
        
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
                'redirect': result.redirect_url
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
        if not wordlist_file.is_absolute():
            # Try to find in wordlists directory
            if self.settings and hasattr(self.settings, 'paths') and 'wordlists' in self.settings.paths:
                wordlist_file = Path(self.settings.paths['wordlists']) / wordlist_path
        
        if wordlist_file.exists():
            with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                return [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            # Treat as comma-separated list
            return [w.strip() for w in wordlist_path.split(',') if w.strip()]