#!/usr/bin/env python3
"""
Comprehensive test for Dirsearch Engine
Tests that the engine doesn't miss basic paths like /admin
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.core.dirsearch_engine import DirsearchEngine, ScanOptions, ScanResult
    from src.models.scan_request import ScanRequest
    from src.config import Settings
    from src.utils.logger import LoggerSetup
except ImportError as e:
    print(f"Import error: {e}")
    print("\nPlease install required dependencies:")
    print("pip install -r requirements.txt")
    sys.exit(1)

class DirsearchEngineTester:
    def __init__(self):
        self.config = Settings()
        self.results: Dict[str, List[ScanResult]] = {}
        self.missing_paths: Dict[str, List[str]] = {}
        
    async def test_basic_paths(self, target_url: str):
        """Test if engine finds basic paths like /admin"""
        print(f"\n{'='*60}")
        print(f"Testing basic path scanning for: {target_url}")
        print(f"{'='*60}\n")
        
        # List of basic paths that should ALWAYS be checked
        critical_paths = [
            'admin',
            'administrator', 
            'login',
            'wp-admin',
            'phpmyadmin',
            'manager',
            'api',
            'config',
            'backup',
            'test',
            'uploads',
            'images',
            'css',
            'js',
            'assets',
            'includes',
            'private',
            'public',
            'tmp',
            'temp'
        ]
        
        # Test with different wordlists
        wordlist_tests = [
            ('common.txt', 'wordlists/common.txt'),
            ('enhanced', 'wordlists/combined-enhanced.txt'),
            ('direct_list', critical_paths)  # Test with direct word list
        ]
        
        for test_name, wordlist in wordlist_tests:
            print(f"\n{'-'*40}")
            print(f"Testing with wordlist: {test_name}")
            print(f"{'-'*40}")
            
            engine = DirsearchEngine(self.config)
            
            # Track found paths
            found_paths = set()
            
            def on_result(result: ScanResult):
                if result.status_code != 404:
                    found_paths.add(result.path.strip('/').lower())
                    print(f"[{result.status_code}] {result.path} ({result.size} bytes)")
            
            # Set callback
            engine.set_result_callback(on_result)
            
            try:
                # Create scan request
                scan_request = ScanRequest(
                    base_url=target_url,
                    wordlist=wordlist if isinstance(wordlist, str) else None,
                    additional_wordlists=[wordlist] if isinstance(wordlist, list) else [],
                    extensions=['php', 'html', 'js', 'txt'],
                    threads=10,
                    timeout=10,
                    follow_redirects=True,
                    exclude_status='404'
                )
                
                # Execute scan
                print(f"Starting scan...")
                response = await engine.execute_scan(scan_request)
                
                print(f"\nScan completed:")
                print(f"  Total requests: {response.statistics.get('total_requests', 0)}")
                print(f"  Findings: {len([r for r in response.results if r['status'] != 404])}")
                print(f"  Errors: {response.statistics.get('errors', 0)}")
                
                # Check which critical paths were found
                missing_critical = []
                for path in critical_paths:
                    if path.lower() not in found_paths:
                        # Also check with extensions
                        path_found = False
                        for ext in ['', '.php', '.html', '.js', '.txt']:
                            if f"{path}{ext}".lower() in found_paths:
                                path_found = True
                                break
                        
                        if not path_found:
                            missing_critical.append(path)
                
                if missing_critical:
                    print(f"\n⚠️  MISSING CRITICAL PATHS:")
                    for path in missing_critical:
                        print(f"    - /{path}")
                    
                    self.missing_paths[test_name] = missing_critical
                else:
                    print(f"\n✅ All critical paths were checked!")
                
                # Store results
                self.results[test_name] = response.results
                
            except Exception as e:
                print(f"\n❌ Error during scan: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                await engine.close()
    
    async def test_path_generation(self):
        """Test path generation logic"""
        print(f"\n{'='*60}")
        print(f"Testing path generation logic")
        print(f"{'='*60}\n")
        
        engine = DirsearchEngine(self.config)
        
        # Test cases
        test_cases = [
            {
                'wordlist': ['admin', 'test', 'config'],
                'extensions': ['php', 'html'],
                'prefixes': [''],
                'suffixes': [''],
                'expected_contains': ['admin', 'admin.php', 'admin.html', 'test', 'test.php', 'config.html']
            },
            {
                'wordlist': ['backup'],
                'extensions': ['zip', 'tar.gz', 'sql'],
                'prefixes': [''],
                'suffixes': [''],
                'expected_contains': ['backup', 'backup.zip', 'backup.tar.gz', 'backup.sql']
            }
        ]
        
        for i, test in enumerate(test_cases):
            print(f"\nTest case {i+1}:")
            print(f"  Wordlist: {test['wordlist']}")
            print(f"  Extensions: {test['extensions']}")
            
            options = ScanOptions(
                extensions=test['extensions'],
                prefixes=test['prefixes'],
                suffixes=test['suffixes']
            )
            
            # Generate paths
            paths = engine._generate_paths(test['wordlist'], options)
            
            print(f"  Generated {len(paths)} paths")
            
            # Check expected paths
            missing = []
            for expected in test['expected_contains']:
                if expected not in paths:
                    missing.append(expected)
            
            if missing:
                print(f"  ⚠️  Missing expected paths: {missing}")
            else:
                print(f"  ✅ All expected paths generated")
            
            # Show sample paths
            print(f"  Sample paths: {paths[:10]}")
        
        await engine.close()
    
    async def test_wordlist_loading(self):
        """Test wordlist loading functionality"""
        print(f"\n{'='*60}")
        print(f"Testing wordlist loading")
        print(f"{'='*60}\n")
        
        engine = DirsearchEngine(self.config)
        
        # Test loading common.txt
        wordlist_path = 'wordlists/common.txt'
        words = engine._load_wordlist(wordlist_path)
        
        print(f"Loaded {len(words)} words from {wordlist_path}")
        
        # Check if critical words are present
        critical_words = ['admin', 'login', 'config', 'backup', 'test']
        missing_words = []
        
        for word in critical_words:
            if word not in words:
                missing_words.append(word)
        
        if missing_words:
            print(f"⚠️  Missing critical words in wordlist: {missing_words}")
        else:
            print(f"✅ All critical words found in wordlist")
        
        # Show sample words
        print(f"\nSample words from wordlist:")
        for word in words[:20]:
            print(f"  - {word}")
        
        await engine.close()
    
    def generate_report(self):
        """Generate test report"""
        print(f"\n{'='*60}")
        print(f"TEST REPORT")
        print(f"{'='*60}\n")
        
        if self.missing_paths:
            print("⚠️  ISSUES FOUND:")
            for test_name, missing in self.missing_paths.items():
                print(f"\n  {test_name}:")
                print(f"    Missing paths: {', '.join(missing)}")
        else:
            print("✅ All tests passed - no missing critical paths")
        
        print(f"\nRECOMMENDATIONS:")
        print("1. Ensure wordlists contain all critical paths")
        print("2. Verify path generation includes all variations")
        print("3. Check that request handling doesn't filter out valid responses")
        print("4. Consider adding intelligent path discovery based on initial findings")


async def main():
    """Main test function"""
    tester = DirsearchEngineTester()
    
    # Test target
    target_url = "http://challenge01.root-me.org/web-serveur/ch4/"
    
    # You can also test with a local server
    # target_url = "http://localhost:8000/"
    
    try:
        # Run tests
        await tester.test_wordlist_loading()
        await tester.test_path_generation()
        await tester.test_basic_paths(target_url)
        
        # Generate report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())