#!/usr/bin/env python3
"""Test case for validating status code detection and preventing 403 false positives"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions, ScanRequest

class StatusCodeValidator:
    """Validate status code detection and prevent false positives"""
    
    def __init__(self):
        self.engine = DirsearchEngine()
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'false_positives': []
        }
    
    async def test_403_detection(self, target_url: str):
        """Test 403 status code detection for false positives"""
        print(f"\n🔍 Testing 403 Detection on: {target_url}")
        print("=" * 60)
        
        # Test paths that commonly cause false 403s
        test_paths = [
            '/test403',
            '/forbidden',
            '/admin',
            '/private',
            '/restricted',
            '/secure',
            '/wp-admin',
            '/.htaccess',
            '/.git',
            '/config',
            '/backup',
            '/api/private',
            '/user/admin',
            '/system',
            '/internal'
        ]
        
        # Configure scan with specific settings for 403 detection
        scan_options = ScanOptions(
            threads=5,
            timeout=10,
            user_agent='Mozilla/5.0 (compatible; StatusCodeTest/1.0)',
            follow_redirects=False,  # Important for accurate status detection
            exclude_status=[404],    # Only exclude 404s
            exclude_sizes=[],        # Don't exclude by size
            exclude_texts=[],        # Don't exclude by text
            extensions=[],           # No extensions for this test
            force_extensions=False,
            lowercase=True,
            uppercase=False,
            capitalization=False,
            recursive=False,         # No recursion for this test
            detect_wildcards=True,   # Enable wildcard detection
            crawl=False
        )
        
        # Create scan request with test paths
        scan_request = ScanRequest(
            url=target_url,
            wordlist=test_paths,
            options=scan_options
        )
        
        print("Test Configuration:")
        print(f"  - Paths to test: {len(test_paths)}")
        print(f"  - Follow redirects: {scan_options.follow_redirects}")
        print(f"  - Detect wildcards: {scan_options.detect_wildcards}")
        print(f"  - Excluded status codes: {scan_options.exclude_status}")
        
        # Execute scan
        print("\nScanning...")
        results = await self.engine.execute_scan(scan_request)
        
        # Analyze results
        status_403_count = 0
        real_403s = []
        potential_false_positives = []
        
        for result in results.results:
            if result['status'] == 403:
                status_403_count += 1
                
                # Check for false positive indicators
                is_false_positive = False
                false_positive_reasons = []
                
                # Check 1: Size-based detection (many false 403s have same size)
                if status_403_count > 3:
                    sizes = [r['size'] for r in results.results if r['status'] == 403]
                    size_frequency = {}
                    for size in sizes:
                        size_frequency[size] = size_frequency.get(size, 0) + 1
                    
                    # If more than 50% have same size, likely false positive
                    max_frequency = max(size_frequency.values())
                    if max_frequency / len(sizes) > 0.5:
                        is_false_positive = True
                        false_positive_reasons.append(f"Common size pattern: {result['size']} bytes")
                
                # Check 2: Generic error page detection
                # This would require response content analysis
                # For now, we'll mark paths that are too generic
                generic_paths = ['/test', '/forbidden', '/restricted', '/private']
                if any(result['path'].startswith(p) for p in generic_paths):
                    # These might be wildcard responses
                    potential_false_positives.append(result)
                else:
                    real_403s.append(result)
        
        # Display results
        print(f"\n📊 Results Summary:")
        print(f"  - Total paths scanned: {len(test_paths)}")
        print(f"  - Total responses: {len(results.results)}")
        print(f"  - 403 responses: {status_403_count}")
        print(f"  - Potential real 403s: {len(real_403s)}")
        print(f"  - Potential false positives: {len(potential_false_positives)}")
        
        if real_403s:
            print("\n✅ Likely Real 403 Forbidden:")
            for r in real_403s[:5]:
                print(f"  - {r['path']} (size: {r['size']} bytes)")
        
        if potential_false_positives:
            print("\n⚠️  Potential False Positives:")
            for r in potential_false_positives[:5]:
                print(f"  - {r['path']} (size: {r['size']} bytes)")
        
        # Wildcard detection test
        await self._test_wildcard_detection(target_url, scan_options)
        
        return {
            'total_403s': status_403_count,
            'real_403s': len(real_403s),
            'false_positives': len(potential_false_positives),
            'results': results
        }
    
    async def _test_wildcard_detection(self, target_url: str, options: ScanOptions):
        """Test wildcard detection to prevent false positives"""
        print("\n🎯 Testing Wildcard Detection:")
        
        # Test with random strings that shouldn't exist
        random_paths = [
            '/asdfghjkl123456',
            '/qwertyuiop987654',
            '/zxcvbnm456789',
            '/randompath123xyz'
        ]
        
        request = ScanRequest(
            url=target_url,
            wordlist=random_paths,
            options=options
        )
        
        results = await self.engine.execute_scan(request)
        
        # Check if all return same status/size (indicating wildcard)
        if results.results:
            statuses = [r['status'] for r in results.results]
            sizes = [r['size'] for r in results.results]
            
            # If all have same status and size, likely wildcard
            if len(set(statuses)) == 1 and len(set(sizes)) == 1:
                print(f"  ⚠️  Wildcard detected! All paths return {statuses[0]} with {sizes[0]} bytes")
                print("  💡 Recommendation: Enable wildcard filtering for this target")
            else:
                print(f"  ✅ No wildcard pattern detected")
                print(f"     Status codes: {set(statuses)}")
                print(f"     Response sizes: {set(sizes)}")
    
    async def test_status_code_accuracy(self, target_url: str):
        """Test overall status code detection accuracy"""
        print(f"\n🔍 Testing Status Code Accuracy on: {target_url}")
        print("=" * 60)
        
        # Test various status codes
        test_cases = {
            'common_files': ['/', '/index.html', '/robots.txt', '/sitemap.xml'],
            'admin_paths': ['/admin/', '/wp-admin/', '/administrator/'],
            'api_paths': ['/api/', '/api/v1/', '/api/users'],
            'backup_files': ['/backup.zip', '/db.sql', '/config.bak'],
            'hidden_files': ['/.git/', '/.env', '/.htaccess']
        }
        
        all_paths = []
        for category, paths in test_cases.items():
            all_paths.extend(paths)
        
        options = ScanOptions(
            threads=10,
            timeout=10,
            follow_redirects=False,
            exclude_status=[404],
            detect_wildcards=True
        )
        
        request = ScanRequest(
            url=target_url,
            wordlist=all_paths,
            options=options
        )
        
        results = await self.engine.execute_scan(request)
        
        # Analyze by category
        print("\n📊 Status Code Distribution:")
        status_distribution = {}
        
        for result in results.results:
            status = result['status']
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        for status, count in sorted(status_distribution.items()):
            print(f"  - {status}: {count} paths")
        
        # Check for suspicious patterns
        print("\n🔍 Pattern Analysis:")
        
        # Check if too many 403s (potential false positives)
        total_results = len(results.results)
        if total_results > 0:
            forbidden_ratio = status_distribution.get(403, 0) / total_results
            if forbidden_ratio > 0.6:
                print(f"  ⚠️  High 403 ratio ({forbidden_ratio:.1%}) - potential false positives")
            else:
                print(f"  ✅ Normal 403 ratio ({forbidden_ratio:.1%})")
        
        return results

async def main():
    """Main test function"""
    validator = StatusCodeValidator()
    
    # Test targets
    test_targets = [
        'http://localhost:8080',  # Local test server
        # Add more test targets as needed
    ]
    
    # Get target from command line if provided
    if len(sys.argv) > 1:
        test_targets = [sys.argv[1]]
    
    for target in test_targets:
        try:
            print(f"\n{'='*60}")
            print(f"🎯 Testing Target: {target}")
            print(f"{'='*60}")
            
            # Test 403 detection
            result_403 = await validator.test_403_detection(target)
            
            # Test overall accuracy
            result_accuracy = await validator.test_status_code_accuracy(target)
            
            print(f"\n✅ Tests completed for {target}")
            
        except Exception as e:
            print(f"\n❌ Error testing {target}: {e}")
    
    print("\n🏁 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())