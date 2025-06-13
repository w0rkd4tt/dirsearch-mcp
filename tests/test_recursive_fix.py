#!/usr/bin/env python3
"""
Test script to verify recursive scanning with proper directory detection
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings

# Mock responses that simulate real directory behavior
MOCK_RESPONSES = {
    # Directories that redirect with 301
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
    
    # Directory listings (after redirect)
    'http://example.com/api/': {
        'status_code': 200,
        'headers': {'content-type': 'text/html'},
        'text': '<html><head><title>Index of /api</title></head><body><h1>Index of /api</h1></body></html>',
        'size': 100
    },
    'http://example.com/admin/': {
        'status_code': 200,
        'headers': {'content-type': 'text/html'},
        'text': '<html><body><h1>Admin Panel</h1></body></html>',
        'size': 50
    },
    
    # Files
    'http://example.com/test.php': {
        'status_code': 200,
        'headers': {'content-type': 'text/html'},
        'text': '<?php echo "test"; ?>',
        'size': 20
    },
    
    # Second level paths
    'http://example.com/api/v1': {
        'status_code': 301,
        'headers': {'location': '/api/v1/', 'content-type': 'text/html'},
        'text': '',
        'size': 0
    },
    'http://example.com/api/v1/': {
        'status_code': 200,
        'headers': {'content-type': 'text/html'},
        'text': '<html><body>API v1</body></html>',
        'size': 30
    },
    'http://example.com/api/users': {
        'status_code': 200,
        'headers': {'content-type': 'application/json'},
        'text': '{"users": []}',
        'size': 13
    },
    'http://example.com/admin/login.php': {
        'status_code': 200,
        'headers': {'content-type': 'text/html'},
        'text': '<form>Login</form>',
        'size': 18
    },
    
    # Third level
    'http://example.com/api/v1/endpoints': {
        'status_code': 200,
        'headers': {'content-type': 'application/json'},
        'text': '{"endpoints": ["users", "posts"]}',
        'size': 33
    }
}

class TestEngine(DirsearchEngine):
    """Engine with mocked responses for testing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_log = []
        self.scan_calls = []
        
    async def _make_request(self, url: str, options: ScanOptions):
        """Return mock responses"""
        self.request_log.append(url)
        
        # Remove trailing slash for lookup if needed
        lookup_url = url.rstrip('/')
        
        # Check both with and without trailing slash
        if url in MOCK_RESPONSES:
            response = MOCK_RESPONSES[url].copy()
        elif lookup_url in MOCK_RESPONSES:
            response = MOCK_RESPONSES[lookup_url].copy()
        else:
            # 404 response
            response = {
                'status_code': 404,
                'headers': {},
                'content': b'Not Found',
                'text': 'Not Found',
                'size': 9,
                'redirect_url': ''
            }
        
        # Add missing fields
        response['content'] = response['text'].encode()
        response['response_time'] = 0.1
        if 'redirect_url' not in response:
            response['redirect_url'] = response.get('headers', {}).get('location', '')
            
        return response
    
    async def _scan_paths(self, base_url: str, paths: list, options: ScanOptions):
        """Log scan calls"""
        self.scan_calls.append({
            'base_url': base_url,
            'path_count': len(paths),
            'sample_paths': paths[:5],
            'recursive': options.recursive
        })
        return await super()._scan_paths(base_url, paths, options)


async def test_recursive_behavior():
    """Test recursive scanning behavior"""
    
    print("Testing Recursive Scanning Behavior")
    print("=" * 50)
    
    settings = Settings()
    engine = TestEngine(settings=settings)
    
    # Initial wordlist
    wordlist = ['api', 'admin', 'test.php', 'v1', 'users', 'login.php', 'endpoints', 'config']
    
    options = ScanOptions(
        recursive=True,
        recursion_depth=3,
        threads=1,
        timeout=5,
        exclude_status_codes=[404],
        detect_wildcards=False,
        follow_redirects=False  # Important: we want to see 301s
    )
    
    print(f"\nInitial wordlist ({len(wordlist)} items): {wordlist}")
    print(f"\nRecursion settings:")
    print(f"  - Enabled: {options.recursive}")
    print(f"  - Max depth: {options.recursion_depth}")
    print(f"  - Follow redirects: {options.follow_redirects}")
    
    try:
        # Run scan
        results = await engine.scan_target('http://example.com', wordlist, options, display_progress=False)
        
        print(f"\n\nScan Results ({len(results)} total):")
        print("-" * 50)
        
        # Group by level
        by_level = {}
        for r in sorted(results, key=lambda x: x.path):
            level = r.path.count('/')
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(r)
        
        for level in sorted(by_level.keys()):
            print(f"\nLevel {level}:")
            for r in by_level[level]:
                dir_marker = "[DIR]" if r.is_directory else "[FILE]"
                print(f"  {dir_marker} {r.path} -> {r.url} [{r.status_code}]")
                if r.redirect_url:
                    print(f"        ↳ Redirects to: {r.redirect_url}")
        
        print(f"\n\nScan Call Summary ({len(engine.scan_calls)} calls):")
        print("-" * 50)
        for i, call in enumerate(engine.scan_calls):
            print(f"\nCall #{i+1}:")
            print(f"  Base URL: {call['base_url']}")
            print(f"  Paths to scan: {call['path_count']}")
            print(f"  Recursive flag: {call['recursive']}")
            print(f"  Sample paths: {call['sample_paths']}")
        
        print(f"\n\nRequest Log ({len(engine.request_log)} requests):")
        print("-" * 50)
        for i, url in enumerate(engine.request_log):
            print(f"  {i+1}. {url}")
        
        # Verify expectations
        print("\n\nVerification:")
        print("-" * 50)
        
        # Check directory detection
        directories = [r for r in results if r.is_directory]
        print(f"\n✓ Directories detected: {len(directories)}")
        for d in directories:
            print(f"  - {d.url} (path: {d.path})")
        
        # Check if api and admin were treated as directories
        api_results = [r for r in results if 'api' in r.path and r.path.count('/') == 1]
        admin_results = [r for r in results if 'admin' in r.path and r.path.count('/') == 1]
        
        print(f"\n✓ /api detection:")
        for r in api_results:
            print(f"  - {r.path} is_directory={r.is_directory} status={r.status_code}")
        
        print(f"\n✓ /admin detection:")  
        for r in admin_results:
            print(f"  - {r.path} is_directory={r.is_directory} status={r.status_code}")
        
        # Check recursive scanning happened
        recursive_bases = set(call['base_url'] for call in engine.scan_calls if not call['base_url'].endswith('example.com'))
        print(f"\n✓ Recursive scans performed on: {len(recursive_bases)} directories")
        for base in sorted(recursive_bases):
            print(f"  - {base}")
        
        # Verify wordlist reuse
        all_same_wordlist = all(call['path_count'] == len(wordlist) for call in engine.scan_calls)
        print(f"\n✓ Same wordlist used for all scans: {all_same_wordlist}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(test_recursive_behavior())