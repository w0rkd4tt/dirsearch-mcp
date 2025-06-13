#!/usr/bin/env python3
"""
Test to see exactly what URLs are being requested during recursive scanning
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
    'http://example.com/api': {'status': 301, 'location': '/api/'},
    'http://example.com/admin': {'status': 301, 'location': '/admin/'},
    'http://example.com/test.php': {'status': 200},
    'http://example.com/api/v1': {'status': 301, 'location': '/api/v1/'},
    'http://example.com/api/users': {'status': 200},
    'http://example.com/admin/login.php': {'status': 200},
}

class DetailedTestEngine(DirsearchEngine):
    """Engine that logs every URL construction"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_log = []
        
    async def _make_request(self, url: str, options: ScanOptions):
        """Log and mock responses"""
        self.url_log.append(url)
        print(f"[REQUEST] {url}")
        
        # Check if URL matches any mock
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
        
        # 404 for everything else
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
        """Log URL construction"""
        full_url = urljoin(base_url, path)
        print(f"[SCAN_PATH] base_url={base_url}, path={path} -> {full_url}")
        return await super()._scan_single_path(base_url, path, *args, **kwargs)


async def test_url_construction():
    """Test URL construction in recursive scanning"""
    
    print("Testing URL Construction in Recursive Scanning")
    print("=" * 60)
    
    settings = Settings()
    engine = DetailedTestEngine(settings=settings)
    
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
    
    print(f"\nWordlist: {wordlist}")
    print(f"Base URL: http://example.com")
    
    try:
        results = await engine.scan_target('http://example.com', wordlist, options, display_progress=False)
        
        print(f"\n\n{'='*60}")
        print("RESULTS")
        print("="*60)
        print(f"\nTotal results: {len(results)}")
        
        for r in results:
            print(f"  {'[DIR]' if r.is_directory else '[FILE]'} {r.url} (path: {r.path}) [{r.status_code}]")
        
        print(f"\n\nAll requested URLs ({len(engine.url_log)}):")
        for i, url in enumerate(engine.url_log, 1):
            print(f"  {i}. {url}")
        
        # Check if subdirectory URLs were constructed correctly
        print(f"\n\nChecking subdirectory URL construction:")
        api_urls = [url for url in engine.url_log if '/api/' in url and url != 'http://example.com/api']
        admin_urls = [url for url in engine.url_log if '/admin/' in url and url != 'http://example.com/admin']
        
        print(f"\nAPI subdirectory URLs ({len(api_urls)}):")
        for url in api_urls:
            print(f"  - {url}")
        
        print(f"\nAdmin subdirectory URLs ({len(admin_urls)}):")
        for url in admin_urls:
            print(f"  - {url}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(test_url_construction())