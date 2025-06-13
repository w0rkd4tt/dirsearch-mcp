#!/usr/bin/env python3
"""
Detailed debug test for recursive scanning
Shows exactly when and how recursive scanning happens
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanOptions
from src.utils.logger import LoggerSetup
from typing import List, Dict, Any


class RecursiveDebugEngine(DirsearchEngine):
    """Extended engine with debug hooks for recursive scanning"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recursive_calls = []
        self.scan_depth = 0
    
    async def _handle_recursive_scan(self, base_url: str, options: ScanOptions, current_depth: int = 0):
        """Override to add debug logging"""
        print(f"\n{'='*60}")
        print(f"🔄 RECURSIVE SCAN TRIGGERED")
        print(f"   Base URL: {base_url}")
        print(f"   Current Depth: {current_depth}")
        print(f"   Max Depth: {options.recursion_depth}")
        print(f"{'='*60}\n")
        
        self.recursive_calls.append({
            'base_url': base_url,
            'depth': current_depth,
            'timestamp': datetime.now()
        })
        
        # Call parent implementation
        await super()._handle_recursive_scan(base_url, options, current_depth)
    
    async def _scan_paths(self, base_url: str, paths: List[str], options: ScanOptions):
        """Override to show when scanning starts for a URL"""
        print(f"\n📍 Scanning {len(paths)} paths at: {base_url}")
        await super()._scan_paths(base_url, paths, options)


async def test_recursive_detailed():
    """Detailed recursive scan test"""
    print("\n" + "="*80)
    print("DETAILED RECURSIVE SCANNING TEST")
    print("="*80)
    
    # Initialize
    LoggerSetup.initialize()
    logger = LoggerSetup.get_logger(__name__)
    engine = RecursiveDebugEngine(logger=logger)
    
    # Target
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    
    # Wordlist focused on finding directories
    wordlist = [
        # Common directories that often exist
        "api", "admin", "images", "css", "js", "static", "public",
        "v1", "v2", "users", "docs", "test", "data", "files",
        # Specific paths that might exist in /api/
        "users", "auth", "login", "status", "health",
        # Some files
        "index.php", "index.html", "test.php", "info.php"
    ]
    
    print(f"\nTarget: {target}")
    print(f"Wordlist: {', '.join(wordlist[:10])}... ({len(wordlist)} total)")
    
    # Options
    options = ScanOptions(
        threads=1,
        timeout=10,
        recursive=True,
        recursion_depth=3,
        detect_wildcards=True,
        follow_redirects=False
    )
    
    print(f"\nSettings:")
    print(f"  • Recursive: {options.recursive}")
    print(f"  • Max Depth: {options.recursion_depth}")
    print(f"  • Threads: {options.threads}")
    
    # Track what we find
    all_directories = []
    paths_by_depth = {0: [], 1: [], 2: [], 3: []}
    
    def on_result(result):
        """Detailed result tracking"""
        if result.status_code not in [404]:
            depth = result.path.strip('/').count('/')
            
            # Track by depth
            if depth <= 3:
                paths_by_depth[depth].append({
                    'path': result.path,
                    'url': result.url,
                    'status': result.status_code,
                    'is_dir': result.is_directory
                })
            
            # Show discovery
            icon = "📁" if result.is_directory else "📄"
            print(f"\n✅ Found: {icon} {result.path} [{result.status_code}] at depth {depth}")
            
            if result.is_directory and result.status_code in [200, 301, 302]:
                all_directories.append(result)
                print(f"   📍 Directory detected! Will be scanned recursively.")
                print(f"   📍 New base URL will be: {result.url}{'/' if not result.url.endswith('/') else ''}")
    
    engine.set_result_callback(on_result)
    
    # Progress tracking
    scan_progress = {'current': 0, 'total': 0}
    
    def on_progress(current, total):
        scan_progress['current'] = current
        scan_progress['total'] = total
    
    engine.set_progress_callback(on_progress)
    
    print("\n" + "="*80)
    print("STARTING SCAN...")
    print("="*80)
    
    try:
        # Run scan
        results = await engine.scan_target(target, wordlist, options, display_progress=True)
        
        # Show detailed results
        print("\n\n" + "="*80)
        print("SCAN COMPLETE - DETAILED ANALYSIS")
        print("="*80)
        
        # Show recursive calls made
        print(f"\n🔄 RECURSIVE SCANS PERFORMED: {len(engine.recursive_calls)}")
        for i, call in enumerate(engine.recursive_calls):
            print(f"\n   {i+1}. Base URL: {call['base_url']}")
            print(f"      Depth: {call['depth']}")
            print(f"      Time: {call['timestamp'].strftime('%H:%M:%S')}")
        
        # Show results by depth
        print("\n📊 RESULTS BY DEPTH LEVEL:")
        for depth in range(4):
            if paths_by_depth[depth]:
                print(f"\n   Level {depth}: {len(paths_by_depth[depth])} results")
                for item in paths_by_depth[depth]:
                    icon = "📁" if item['is_dir'] else "📄"
                    print(f"      {icon} {item['path']} [{item['status']}]")
        
        # Directory tree
        print("\n🌳 DIRECTORY TREE:")
        tree = build_tree(results)
        print_tree(tree)
        
        # Verify recursion
        print("\n✅ RECURSION VERIFICATION:")
        nested = [r for r in results if r.path.count('/') >= 2]
        if nested:
            print(f"   Found {len(nested)} nested paths - recursion is working!")
            for r in nested[:5]:
                print(f"   • {r.path} [{r.status_code}]")
        else:
            print("   ⚠️  No nested paths found")
        
        # Statistics
        print(f"\n📈 STATISTICS:")
        print(f"   Total Results: {len(results)}")
        print(f"   Directories Found: {len(all_directories)}")
        print(f"   Recursive Scans: {len(engine.recursive_calls)}")
        stats = engine.get_scan_statistics()
        print(f"   Total Requests: {stats.total_requests}")
        print(f"   Duration: {stats.duration:.2f}s")
        
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


def build_tree(results):
    """Build directory tree from results"""
    tree = {'': {'_files': [], '_dirs': {}}}
    
    for r in results:
        if r.status_code not in [404]:
            parts = r.path.strip('/').split('/')
            current = tree['']['_dirs']
            
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {'_files': [], '_dirs': {}}
                current = current[part]['_dirs']
            
            if parts:
                final = parts[-1]
                if r.is_directory:
                    if final not in current:
                        current[final] = {'_files': [], '_dirs': {}}
                else:
                    if '_files' not in current:
                        current['_files'] = []
                    current['_files'].append(final)
    
    return tree


def print_tree(tree, prefix="", name="", is_last=True):
    """Print directory tree"""
    if name:
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{name}/")
        prefix += "    " if is_last else "│   "
    
    dirs = tree.get(name, tree.get('', {})).get('_dirs', {})
    files = tree.get(name, tree.get('', {})).get('_files', [])
    
    # Print directories
    dir_items = list(dirs.items())
    for i, (dirname, subdir) in enumerate(dir_items):
        is_last_dir = i == len(dir_items) - 1 and not files
        print_tree(subdir, prefix, dirname, is_last_dir)
    
    # Print files
    for i, filename in enumerate(files):
        connector = "└── " if i == len(files) - 1 else "├── "
        print(f"{prefix}{connector}{filename}")


if __name__ == "__main__":
    print("""
Detailed Recursive Scanning Debug

This test shows exactly when and how recursive scanning occurs.

Usage:
    python test_recursive_detailed.py                    # Scan localhost:8080
    python test_recursive_detailed.py http://example.com # Scan custom target
""")
    
    import asyncio
    asyncio.run(test_recursive_detailed())