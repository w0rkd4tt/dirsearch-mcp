#!/usr/bin/env python3
"""
Complete test of recursive scanning showing full depth traversal
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

# Mock responses for complete recursive test
MOCK_RESPONSES = {
    # Level 0 - Root
    'http://example.com/api': {
        'status_code': 301,
        'headers': {'location': '/api/', 'content-type': 'text/html'},
        'text': '',
        'size': 0
    },
    'http://example.com/admin': {
        'status_code': 301,
        'headers': {'location': '/admin/', 'content-type': 'text/html'},
        'text': '',
        'size': 0
    },
    'http://example.com/test.php': {
        'status_code': 200,
        'headers': {'content-type': 'text/html'},
        'text': 'test file',
        'size': 9
    },
    
    # Level 1 - Inside /api/
    'http://example.com/api/v1': {
        'status_code': 301,
        'headers': {'location': '/api/v1/', 'content-type': 'text/html'},
        'text': '',
        'size': 0
    },
    'http://example.com/api/users': {
        'status_code': 200,
        'headers': {'content-type': 'application/json'},
        'text': '{"users": []}',
        'size': 13
    },
    
    # Level 1 - Inside /admin/
    'http://example.com/admin/login.php': {
        'status_code': 200,
        'headers': {'content-type': 'text/html'},
        'text': '<form>Login</form>',
        'size': 18
    },
    
    # Level 2 - Inside /api/v1/
    'http://example.com/api/v1/endpoints': {
        'status_code': 200,
        'headers': {'content-type': 'application/json'},
        'text': '{"endpoints": []}',
        'size': 17
    },
    'http://example.com/api/v1/users': {
        'status_code': 200,
        'headers': {'content-type': 'application/json'},
        'text': '{"v1_users": []}',
        'size': 16
    }
}

class VerboseTestEngine(DirsearchEngine):
    """Engine with detailed logging for debugging"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_requests = []
        self.scan_history = []
        
    async def _make_request(self, url: str, options: ScanOptions):
        """Return mock responses with logging"""
        self.all_requests.append(url)
        
        # Default 404
        response = {
            'status_code': 404,
            'headers': {},
            'content': b'Not Found',
            'text': 'Not Found',
            'size': 9,
            'response_time': 0.1,
            'redirect_url': ''
        }
        
        # Check for mock response
        if url in MOCK_RESPONSES:
            response = MOCK_RESPONSES[url].copy()
            response['content'] = response['text'].encode()
            response['response_time'] = 0.1
            if 'redirect_url' not in response:
                response['redirect_url'] = response.get('headers', {}).get('location', '')
        
        return response
    
    async def _scan_paths(self, base_url: str, paths: list, options: ScanOptions):
        """Track all scan operations"""
        scan_info = {
            'base_url': base_url,
            'paths': paths.copy(),
            'recursive': options.recursive,
            'results_before': len(self._results)
        }
        
        result = await super()._scan_paths(base_url, paths, options)
        
        scan_info['results_after'] = len(self._results)
        scan_info['new_results'] = scan_info['results_after'] - scan_info['results_before']
        self.scan_history.append(scan_info)
        
        return result
    
    async def _handle_recursive_scan(self, base_url: str, options: ScanOptions, current_depth: int = 0):
        """Log recursive scan details"""
        print(f"\n[RECURSIVE SCAN] Depth: {current_depth}/{options.recursion_depth}")
        print(f"[RECURSIVE SCAN] Base URL: {base_url}")
        print(f"[RECURSIVE SCAN] Current results: {len(self._results)}")
        
        # Show current directories
        dirs = [r for r in self._results if r.is_directory]
        print(f"[RECURSIVE SCAN] Current directories ({len(dirs)}):")
        for d in dirs:
            scanned = d.url in getattr(self, '_deep_scanned_dirs', set())
            print(f"  - {d.url} (scanned: {scanned})")
        
        await super()._handle_recursive_scan(base_url, options, current_depth)


async def test_full_recursive():
    """Test complete recursive scanning"""
    
    print("Complete Recursive Scanning Test")
    print("=" * 60)
    
    settings = Settings()
    engine = VerboseTestEngine(settings=settings)
    
    # Wordlist that will find items at each level
    wordlist = [
        # Level 0
        'api', 'admin', 'test.php',
        # Level 1
        'v1', 'users', 'login.php',
        # Level 2
        'endpoints',
        # Extra
        'config', 'backup'
    ]
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=3,  # Allow 3 levels
        threads=1,
        timeout=5,
        exclude_status_codes=[404],
        detect_wildcards=False,
        follow_redirects=False
    )
    
    print(f"\nSettings:")
    print(f"  Wordlist: {len(wordlist)} items")
    print(f"  Recursive: {options.recursive}")
    print(f"  Max depth: {options.recursion_depth}")
    
    try:
        # Run scan
        results = await engine.scan_target('http://example.com', wordlist, options, display_progress=False)
        
        print(f"\n\n{'='*60}")
        print("FINAL RESULTS")
        print("="*60)
        print(f"\nTotal found: {len(results)} paths")
        
        # Organize by depth
        by_depth = {}
        for r in results:
            depth = r.path.count('/')
            if r.path.endswith('/'):
                depth -= 1
            if depth not in by_depth:
                by_depth[depth] = []
            by_depth[depth].append(r)
        
        # Display tree structure
        print("\nDirectory Tree:")
        print("http://example.com/")
        
        for depth in sorted(by_depth.keys()):
            items = sorted(by_depth[depth], key=lambda x: x.path)
            for item in items:
                indent = "  " * (depth + 1)
                marker = "📁" if item.is_directory else "📄"
                status = f"[{item.status_code}]"
                print(f"{indent}{marker} {item.path} {status}")
        
        # Scan history
        print(f"\n\n{'='*60}")
        print("SCAN HISTORY")
        print("="*60)
        print(f"\nTotal scan operations: {len(engine.scan_history)}")
        
        for i, scan in enumerate(engine.scan_history):
            print(f"\nScan #{i+1}:")
            print(f"  Base URL: {scan['base_url']}")
            print(f"  Paths scanned: {len(scan['paths'])}")
            print(f"  Recursive: {scan['recursive']}")
            print(f"  New results: {scan['new_results']}")
            if scan['new_results'] > 0:
                print(f"  Found items: ", end="")
                # Show what was found in this scan
                start_idx = scan['results_before']
                end_idx = scan['results_after']
                found_items = [r.path for r in results[start_idx:end_idx]]
                print(", ".join(found_items))
        
        # Verify expectations
        print(f"\n\n{'='*60}")
        print("VERIFICATION")
        print("="*60)
        
        # Check each level
        level_0 = [r for r in results if r.path.count('/') == 0]
        level_1 = [r for r in results if r.path.count('/') == 1]
        level_2 = [r for r in results if r.path.count('/') == 2]
        
        print(f"\n✓ Level 0 (root): {len(level_0)} items")
        for item in level_0:
            print(f"  - {item.path} ({'DIR' if item.is_directory else 'FILE'})")
        
        print(f"\n✓ Level 1: {len(level_1)} items")
        for item in level_1:
            print(f"  - {item.path} ({'DIR' if item.is_directory else 'FILE'})")
        
        print(f"\n✓ Level 2: {len(level_2)} items")
        for item in level_2:
            print(f"  - {item.path} ({'DIR' if item.is_directory else 'FILE'})")
        
        # Check if recursive scanning worked properly
        print(f"\n✓ Recursive scanning summary:")
        dirs_found = [r for r in results if r.is_directory]
        print(f"  - Directories found: {len(dirs_found)}")
        print(f"  - Max depth reached: {max(r.path.count('/') for r in results)}")
        print(f"  - Total requests made: {len(engine.all_requests)}")
        
        # Expected vs actual
        expected_paths = [
            'api', 'admin', 'test.php',  # Level 0
            'api/v1', 'api/users', 'admin/login.php',  # Level 1
            'api/v1/endpoints', 'api/v1/users'  # Level 2
        ]
        
        found_paths = [r.path for r in results]
        print(f"\n✓ Expected paths coverage:")
        for exp in expected_paths:
            found = exp in found_paths
            print(f"  - {exp}: {'✅' if found else '❌'}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(test_full_recursive())