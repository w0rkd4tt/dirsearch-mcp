#!/usr/bin/env python3
"""
Test to debug the _scanned_paths filtering issue
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

# Mock responses
MOCK_RESPONSES = {
    'http://example.com/api': {'status': 301, 'location': '/api/'},
    'http://example.com/admin': {'status': 301, 'location': '/admin/'},
    'http://example.com/test.php': {'status': 200},
    'http://example.com/api/v1': {'status': 301, 'location': '/api/v1/'},
    'http://example.com/api/users': {'status': 200},
    'http://example.com/admin/login.php': {'status': 200},
}

class DebuggingEngine(DirsearchEngine):
    """Engine that debugs path filtering"""
    
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
    
    async def _scan_single_path(self, base_url: str, path: str, *args, **kwargs):
        """Debug path filtering"""
        print(f"\n[_scan_single_path] base_url={base_url}, path={path}")
        
        # Check if path is already scanned
        with self._lock:
            already_scanned = path in self._scanned_paths
            print(f"  Already scanned? {already_scanned}")
            print(f"  Current _scanned_paths ({len(self._scanned_paths)}): {list(self._scanned_paths)[:5]}...")
        
        result = await super()._scan_single_path(base_url, path, *args, **kwargs)
        
        if result:
            print(f"  Result: {result.url} [{result.status_code}]")
        else:
            print(f"  Result: None")
        
        return result
    
    async def _handle_recursive_scan(self, base_url: str, options: ScanOptions, current_depth: int = 0):
        """Debug recursive scanning"""
        print(f"\n[RECURSIVE] Starting at depth {current_depth}")
        print(f"[RECURSIVE] _scanned_paths has {len(self._scanned_paths)} items")
        
        # Clear scanned paths for subdirectories to allow scanning
        # This is the key insight - paths are being marked as scanned globally
        # but we need to scan them again in different directories
        
        await super()._handle_recursive_scan(base_url, options, current_depth)


async def test_scanned_paths_issue():
    """Test the _scanned_paths filtering issue"""
    
    print("Testing _scanned_paths Filtering Issue")
    print("=" * 60)
    
    settings = Settings()
    engine = DebuggingEngine(settings=settings)
    
    wordlist = ['api', 'admin', 'test.php', 'v1', 'users', 'login.php']
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=2,
        threads=1,
        timeout=5,
        exclude_status_codes=[404],
        detect_wildcards=False,
        follow_redirects=False
    )
    
    try:
        results = await engine.scan_target('http://example.com', wordlist, options, display_progress=False)
        
        print(f"\n\n{'='*60}")
        print("ANALYSIS")
        print("="*60)
        
        print(f"\nTotal results: {len(results)}")
        for r in results:
            print(f"  {r.url} [{r.status_code}]")
        
        print(f"\nFinal _scanned_paths ({len(engine._scanned_paths)}):")
        for path in sorted(engine._scanned_paths):
            print(f"  - {path}")
        
        print("\n\nISSUE IDENTIFIED:")
        print("The problem is that _scanned_paths stores just the path (e.g., 'users')")
        print("without the directory context. So when we scan /api/, the path 'users'")
        print("is already marked as scanned from the root scan, preventing /api/users")
        print("from being checked!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(test_scanned_paths_issue())