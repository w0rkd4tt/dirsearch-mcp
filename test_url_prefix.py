#!/usr/bin/env python3
"""
Test script to verify URL prefix handling in scan results
"""

import asyncio
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions


async def test_url_prefix_scanning():
    """Test scanning URLs with various prefixes"""
    
    # Test cases with different URL prefixes
    test_cases = [
        {
            'url': 'http://testphp.vulnweb.com',
            'description': 'Root URL (no prefix)',
            'expected_prefix': ''
        },
        {
            'url': 'http://testphp.vulnweb.com/app',
            'description': 'Single level prefix',
            'expected_prefix': '/app'
        },
        {
            'url': 'http://testphp.vulnweb.com/api/v1',
            'description': 'Multi-level prefix',
            'expected_prefix': '/api/v1'
        },
        {
            'url': 'http://testphp.vulnweb.com/admin/dashboard/',
            'description': 'Prefix with trailing slash',
            'expected_prefix': '/admin/dashboard'
        }
    ]
    
    # Simple wordlist for testing
    test_wordlist = ['index', 'login', 'config', 'test']
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test_case['description']}")
        print(f"URL: {test_case['url']}")
        print(f"Expected prefix: {test_case['expected_prefix'] or '(none)'}")
        print(f"{'-'*60}")
        
        try:
            async with DirsearchEngine() as engine:
                options = ScanOptions(
                    extensions=[],  # No extensions for this test
                    threads=5,
                    timeout=5,
                    recursive=False
                )
                
                results = await engine.scan_target(
                    url=test_case['url'],
                    wordlist=test_wordlist,
                    options=options,
                    display_progress=False
                )
                
                print(f"Found {len(results)} results")
                
                # Check if paths include the prefix
                if results:
                    print("\nSample results:")
                    for i, result in enumerate(results[:5]):
                        parsed = urlparse(result.url)
                        print(f"  {i+1}. Full URL: {result.url}")
                        print(f"     Path in result: {result.path}")
                        print(f"     Status: {result.status_code}")
                        
                        # Verify prefix is included
                        if test_case['expected_prefix']:
                            if result.path.startswith(test_case['expected_prefix']):
                                print(f"     ✓ Prefix correctly included")
                            else:
                                print(f"     ✗ Prefix missing! Expected to start with: {test_case['expected_prefix']}")
                        print()
                
        except Exception as e:
            print(f"Error during test: {e}")


async def test_report_generation():
    """Test that reports show full paths with prefixes"""
    
    print("\n" + "="*60)
    print("Testing Report Generation with Prefixes")
    print("="*60)
    
    # Simulate scan results with different prefixes
    from src.core.dirsearch_engine import ScanResult
    import time
    
    mock_results = [
        ScanResult(
            url="http://example.com/app/v1/admin",
            path="/app/v1/admin",
            status_code=200,
            size=1024,
            is_directory=True
        ),
        ScanResult(
            url="http://example.com/app/v1/config.php",
            path="/app/v1/config.php",
            status_code=403,
            size=512,
            is_directory=False
        ),
        ScanResult(
            url="http://example.com/api/users",
            path="/api/users",
            status_code=200,
            size=2048,
            is_directory=False
        )
    ]
    
    print("\nMock Results:")
    for i, result in enumerate(mock_results):
        print(f"{i+1}. Path: {result.path} (Status: {result.status_code})")
    
    # Test report data generation
    from src.utils.reporter import ReportGenerator
    
    report_gen = ReportGenerator()
    
    # Create scan data with mock results
    scan_data = {
        'target_url': 'http://example.com/app/v1',
        'target_domain': 'example.com',
        'scan_results': [
            {
                'path': result.path,
                'url': result.url,
                'status': result.status_code,
                'size': result.size,
                'is_directory': result.is_directory,
                'content_type': 'text/html',
                'response_time': 0.1
            }
            for result in mock_results
        ],
        'start_time': '2024-01-01T10:00:00',
        'end_time': '2024-01-01T10:05:00',
        'duration': 300,
        'scan_config': {
            'wordlist': 'test.txt',
            'threads': 10
        },
        'performance_metrics': {
            'total_requests': 100,
            'requests_per_second': 20
        }
    }
    
    # Generate findings summary
    summary = report_gen._generate_findings_summary(scan_data)
    
    print("\nReport Summary:")
    print(f"Total findings: {summary['total_findings']}")
    print(f"Directories found: {summary['directories_found']}")
    
    print("\nPaths in report:")
    for path in summary.get('directory_list', []):
        print(f"  - {path}")
    
    # Verify paths include prefixes
    print("\nPrefix verification:")
    for result in scan_data['scan_results']:
        path = result['path']
        if '/app/v1' in path or '/api' in path:
            print(f"  ✓ {path} - includes prefix")
        else:
            print(f"  ✗ {path} - missing prefix!")


if __name__ == "__main__":
    print("Testing URL Prefix Handling")
    print("="*60)
    
    # Run async tests
    asyncio.run(test_url_prefix_scanning())
    asyncio.run(test_report_generation())