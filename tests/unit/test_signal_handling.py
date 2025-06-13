#!/usr/bin/env python3
"""
Test script to verify Ctrl+C signal handling on macOS
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.dirsearch_engine import DirsearchEngine, ScanRequest
from src.config.settings import Settings
from src.utils.logger import LoggerSetup


async def test_scan_with_interrupt():
    """Test scan that can be interrupted with Ctrl+C"""
    print("Starting test scan...")
    print("Press Ctrl+C to test interrupt handling\n")
    
    # Initialize components
    settings = Settings()
    LoggerSetup.initialize()
    engine = DirsearchEngine(settings)
    
    # Create a long-running scan request
    scan_request = ScanRequest(
        base_url="https://httpbin.org",
        wordlist="common.txt",
        extensions=["php", "html", "js", "txt"],
        threads=5,
        timeout=10,
        delay=0.5,  # Add delay to make it easier to interrupt
        recursive=True,
        recursion_depth=3
    )
    
    print("Scan configuration:")
    print(f"  Target: {scan_request.base_url}")
    print(f"  Wordlist: {scan_request.wordlist}")
    print(f"  Extensions: {', '.join(scan_request.extensions)}")
    print(f"  Threads: {scan_request.threads}")
    print(f"  Delay: {scan_request.delay}s between requests")
    print("\nStarting scan...")
    
    # Track progress
    def on_progress(current, total):
        print(f"\rProgress: {current}/{total} ({current/total*100:.1f}%)", end="", flush=True)
    
    def on_result(result):
        print(f"\nFound: [{result.status_code}] {result.path}")
    
    engine.set_progress_callback(on_progress)
    engine.set_result_callback(on_result)
    
    try:
        start_time = time.time()
        response = await engine.execute_scan(scan_request)
        
        print(f"\n\nScan completed successfully!")
        print(f"Duration: {time.time() - start_time:.1f}s")
        print(f"Total requests: {response.statistics['total_requests']}")
        print(f"Found paths: {response.statistics['found_paths']}")
        
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user (Ctrl+C)")
        print("Graceful shutdown completed")
        return True
    except asyncio.CancelledError:
        print("\n\nScan cancelled")
        print("Graceful shutdown completed")
        return True
    except Exception as e:
        print(f"\n\nError during scan: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.close()
    
    return False


async def test_interactive_mode():
    """Test interactive mode with Ctrl+C handling"""
    print("\nTesting interactive mode...")
    print("Press Ctrl+C to test interrupt handling\n")
    
    from src.cli.interactive_menu import InteractiveMenu
    
    try:
        menu = InteractiveMenu()
        await menu._async_run()
    except KeyboardInterrupt:
        print("\nInteractive mode interrupted successfully")
        return True
    except Exception as e:
        print(f"\nError in interactive mode: {e}")
        return False
    
    return False


def main():
    """Main test function"""
    print("=" * 60)
    print("Dirsearch MCP - Signal Handling Test")
    print("=" * 60)
    print("\nThis test will verify that Ctrl+C works properly on macOS")
    print("during async scan operations.\n")
    
    test_choice = input("Select test:\n1. Test scan interruption\n2. Test interactive mode\nChoice (1/2): ")
    
    if test_choice == "1":
        # Test scan interruption
        try:
            interrupted = asyncio.run(test_scan_with_interrupt())
            if interrupted:
                print("\n✅ Signal handling test PASSED")
                print("Ctrl+C properly stopped the scan")
            else:
                print("\n❌ Signal handling test FAILED")
                print("Scan completed without interruption")
        except KeyboardInterrupt:
            print("\n✅ Signal handling test PASSED")
            print("Ctrl+C properly handled at top level")
    
    elif test_choice == "2":
        # Test interactive mode
        try:
            interrupted = asyncio.run(test_interactive_mode())
            if interrupted:
                print("\n✅ Interactive mode signal handling test PASSED")
            else:
                print("\n❌ Interactive mode signal handling test FAILED")
        except KeyboardInterrupt:
            print("\n✅ Interactive mode signal handling test PASSED")
            print("Ctrl+C properly handled")
    
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()