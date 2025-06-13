#!/usr/bin/env python3
"""
Demonstration of all dirsearch features
Can be used with any accessible target URL
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.config.settings import Settings


async def demonstrate_features(target_url=None):
    """Demonstrate all migrated features"""
    
    if not target_url:
        print("\nDirsearch Features Demonstration")
        print("================================")
        print("\nNote: The Root-Me server appears to be inaccessible.")
        print("You can run this demo with your own target:")
        print("  python test_features_demo.py http://your-target.com/")
        print("\nAlternatively, here's how each feature works:\n")
    else:
        print(f"\nTesting all dirsearch features on: {target_url}")
        print("="*60)
    
    engine = DirsearchEngine(Settings())
    
    # 1. Extension Tags Demo
    print("\n1. Extension Tags Feature (%EXT%)")
    print("-" * 30)
    wordlist_with_tags = [
        "admin.%EXT%",
        "config.%EXT%",
        "backup.%EXT%"
    ]
    extensions = ['php', 'asp', 'jsp', 'html']
    
    enhanced = engine._enhance_wordlist_with_extensions(
        wordlist_with_tags, 
        extensions, 
        '%EXT%'
    )
    
    print(f"Original: {wordlist_with_tags}")
    print(f"Extensions: {extensions}")
    print(f"Enhanced to {len(enhanced)} paths:")
    for path in sorted(enhanced)[:6]:
        print(f"  - {path}")
    print("  ...")
    
    # 2. Dynamic Content Parser Demo
    print("\n2. Dynamic Content/Wildcard Detection")
    print("-" * 30)
    from src.core.dirsearch_engine import DynamicContentParser
    
    # Example of dynamic content
    content1 = "Error 404: Page not found - Request ID: 12345"
    content2 = "Error 404: Page not found - Request ID: 67890"
    
    parser = DynamicContentParser(content1, content2)
    print(f"Content 1: {content1}")
    print(f"Content 2: {content2}")
    print(f"Is static: {parser._is_static}")
    
    # Test with new content
    content3 = "Error 404: Page not found - Request ID: 99999"
    matches = parser.compare_to(content3)
    print(f"Content 3: {content3}")
    print(f"Matches pattern: {matches}")
    print("\nThis helps filter out false positives from dynamic 404 pages!")
    
    # 3. Authentication Support Demo
    print("\n3. Authentication Methods")
    print("-" * 30)
    auth_types = {
        'basic': 'Basic HTTP Authentication',
        'digest': 'Digest Authentication (more secure)',
        'ntlm': 'NTLM Authentication (Windows domains)'
    }
    
    for auth_type, description in auth_types.items():
        handler = engine._get_auth_handler(auth_type, ('user', 'pass'))
        status = "✅ Available" if handler else "❌ Not installed"
        print(f"{auth_type.upper()}: {description} - {status}")
    
    # 4. Blacklist Rules Demo
    print("\n4. Blacklist Filtering")
    print("-" * 30)
    blacklist_rules = {
        403: ['cgi-bin', 'icons', '.ht'],
        500: ['error', 'debug', 'trace']
    }
    
    test_paths = [
        ('cgi-bin/test.cgi', 403, True),
        ('admin/panel.php', 403, False),
        ('error.log', 500, True),
        ('index.php', 200, False)
    ]
    
    options = ScanOptions(blacklists=blacklist_rules)
    
    print("Blacklist rules:")
    for status, patterns in blacklist_rules.items():
        print(f"  {status}: {', '.join(patterns)}")
    
    print("\nTest results:")
    for path, status, expected in test_paths:
        is_blacklisted = engine._is_blacklisted(path, status, options)
        result = "Filtered" if is_blacklisted else "Allowed"
        print(f"  {path} [{status}] → {result}")
    
    # 5. Random User Agents Demo
    print("\n5. Random User Agents")
    print("-" * 30)
    user_agents = set()
    for _ in range(5):
        ua = engine._get_random_user_agent()
        user_agents.add(ua)
    
    print(f"Found {len(user_agents)} different user agents")
    print("Samples:")
    for ua in list(user_agents)[:3]:
        print(f"  - {ua[:70]}...")
    
    # 6. Path Generation Demo
    print("\n6. Complete Path Generation")
    print("-" * 30)
    demo_wordlist = [
        "admin.%EXT%",  # Will be expanded
        "login",        # Will get extensions added
        "test"          # Will get extensions added
    ]
    
    options = ScanOptions(
        extensions=['php', 'html'],
        extension_tag='%EXT%'
    )
    
    paths = engine._generate_paths(demo_wordlist, options)
    print(f"Original wordlist: {demo_wordlist}")
    print(f"Generated {len(paths)} total paths:")
    for path in sorted(paths)[:10]:
        print(f"  - {path}")
    
    # 7. If target URL provided, run actual scan
    if target_url:
        print("\n7. Running Actual Scan")
        print("-" * 30)
        
        wordlist = [
            "admin.%EXT%",
            "config.%EXT%",
            "login.%EXT%",
            "index",
            "robots.txt",
            "sitemap.xml"
        ]
        
        scan_options = ScanOptions(
            extensions=['php', 'html', 'asp', 'txt'],
            extension_tag='%EXT%',
            detect_wildcards=True,
            crawl=True,
            random_user_agents=True,
            blacklists={403: ['cgi-bin'], 500: ['error']},
            threads=10,
            timeout=15,
            exclude_status_codes=[404]
        )
        
        try:
            print(f"Scanning {target_url} with all features enabled...")
            
            # Check for wildcards first
            wildcard = await engine._detect_wildcard(target_url, scan_options)
            if wildcard and wildcard.get('detected'):
                print(f"⚠️  Wildcard detected for status {wildcard['status']}")
            
            # Run scan
            results = await engine.scan_target(target_url, wordlist, scan_options)
            
            if results:
                print(f"\n✅ Found {len(results)} paths:")
                for result in results[:10]:
                    print(f"  [{result.status_code}] {result.path} ({result.size} bytes)")
                if len(results) > 10:
                    print(f"  ... and {len(results) - 10} more")
                    
                # Show crawled paths
                if engine._crawled_paths:
                    print(f"\nCrawled {len(engine._crawled_paths)} additional paths")
            else:
                print("\n❌ No paths found")
                
        except Exception as e:
            print(f"\n❌ Scan error: {e}")
    
    await engine.close()
    
    print("\n" + "="*60)
    print("Feature demonstration completed!")


async def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        await demonstrate_features(target_url)
    else:
        await demonstrate_features()


if __name__ == "__main__":
    asyncio.run(main())