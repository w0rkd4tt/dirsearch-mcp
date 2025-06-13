#!/usr/bin/env python3
"""
Demonstrate the fix for recursive scanning by storing full paths in _scanned_paths
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings
from urllib.parse import urljoin

# Mock responses
MOCK_RESPONSES = {
    # Root level
    'http://example.com/api': {'status': 301, 'location': '/api/'},
    'http://example.com/admin': {'status': 301, 'location': '/admin/'},
    'http://example.com/test.php': {'status': 200},
    'http://example.com/users': {'status': 200},  # users at root
    
    # Inside /api/
    'http://example.com/api/v1': {'status': 301, 'location': '/api/v1/'},
    'http://example.com/api/users': {'status': 200},  # users in api
    'http://example.com/api/test.php': {'status': 200},  # test.php in api
    
    # Inside /admin/
    'http://example.com/admin/login.php': {'status': 200},
    'http://example.com/admin/users': {'status': 200},  # users in admin
    
    # Inside /api/v1/
    'http://example.com/api/v1/users': {'status': 200},  # users in api/v1
    'http://example.com/api/v1/endpoints': {'status': 200},
}

class FixedEngine(DirsearchEngine):
    """Engine with fixed _scanned_paths behavior"""
    
    async def _make_request(self, url: str, options: ScanOptions):
        """Mock responses"""
        for mock_url, mock_data in MOCK_RESPONSES.items():
            if url == mock_url:
                return {
                    'status_code': mock_data['status'],
                    'headers': {
                        'content-type': 'text/html',
                        'location': mock_data.get('location', '')
                    },
                    'content': b'test',
                    'text': 'test',
                    'size': 4,
                    'response_time': 0.1,
                    'redirect_url': mock_data.get('location', '')
                }
        
        return {
            'status_code': 404,
            'headers': {},
            'content': b'',
            'text': '',
            'size': 0,
            'response_time': 0.1,
            'redirect_url': ''
        }
    
    async def _scan_single_path(self, base_url, path, options, semaphore, current, total):
        """Override to fix the scanned paths issue"""
        async with semaphore:
            # FIXED: Store full URL instead of just path
            url = urljoin(base_url, path)
            
            # Skip if already scanned (check full URL, not just path)
            with self._lock:
                if url in self._scanned_paths:
                    return None
                self._scanned_paths.add(url)  # Store full URL
            
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
                        await asyncio.sleep(2 ** attempt)
            
            with self._lock:
                self._stats.total_requests += 1
        
        return None


async def test_fixed_recursive():
    """Test the fixed recursive scanning"""
    
    print("Testing Fixed Recursive Scanning")
    print("=" * 60)
    
    settings = Settings()
    engine = FixedEngine(settings=settings)
    
    wordlist = ['api', 'admin', 'test.php', 'v1', 'users', 'login.php', 'endpoints']
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=3,
        threads=1,
        timeout=5,
        exclude_status_codes=[404],
        detect_wildcards=False,
        follow_redirects=False
    )
    
    print(f"\nScanning with fixed _scanned_paths behavior")
    print(f"Wordlist: {wordlist}")
    
    try:
        results = await engine.scan_target('http://example.com', wordlist, options, display_progress=False)
        
        print(f"\n\n{'='*60}")
        print("RESULTS WITH FIX")
        print("="*60)
        print(f"\nTotal found: {len(results)} paths")
        
        # Group by directory
        by_directory = {}
        for r in results:
            # Extract directory from URL
            parts = r.url.replace('http://example.com/', '').split('/')
            if len(parts) == 1:
                dir_key = '/'
            else:
                dir_key = '/' + '/'.join(parts[:-1]) + '/'
            
            if dir_key not in by_directory:
                by_directory[dir_key] = []
            by_directory[dir_key].append(r)
        
        # Display results by directory
        for dir_path in sorted(by_directory.keys()):
            print(f"\nIn {dir_path}:")
            for r in sorted(by_directory[dir_path], key=lambda x: x.path):
                marker = "📁" if r.is_directory else "📄"
                print(f"  {marker} {r.path} [{r.status_code}]")
        
        # Show that duplicate filenames were found in different directories
        print(f"\n\nDuplicate filename analysis:")
        filenames = {}
        for r in results:
            filename = r.path.split('/')[-1]
            if filename not in filenames:
                filenames[filename] = []
            filenames[filename].append(r.url)
        
        for filename, urls in filenames.items():
            if len(urls) > 1:
                print(f"\n'{filename}' found in {len(urls)} locations:")
                for url in urls:
                    print(f"  - {url}")
        
        print(f"\n\nFinal _scanned_paths ({len(engine._scanned_paths)} entries):")
        # Show first few entries
        for i, path in enumerate(sorted(engine._scanned_paths)):
            if i < 10:
                print(f"  - {path}")
            elif i == 10:
                print(f"  ... and {len(engine._scanned_paths) - 10} more")
                break
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    import time
    asyncio.run(test_fixed_recursive())