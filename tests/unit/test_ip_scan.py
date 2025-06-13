#!/usr/bin/env python3
"""Test scanning IP addresses"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.mcp_coordinator import MCPCoordinator
from src.config.settings import Settings

async def test_ip_scan():
    settings = Settings()
    mcp = MCPCoordinator(settings)
    
    # Initialize MCP
    await mcp.initialize()
    
    # Test with IP address
    test_targets = [
        "192.168.214.143",
        "http://192.168.214.143",
        "https://192.168.214.143",
        "192.168.214.143:8080",
        "http://192.168.214.143:8080"
    ]
    
    for target in test_targets:
        print(f"\nTesting target: {target}")
        try:
            target_info = await mcp.analyze_target(target)
            print(f"  URL: {target_info.url}")
            print(f"  Domain: {target_info.domain}")
            print(f"  Server: {target_info.server_type}")
            print(f"  Success!")
        except Exception as e:
            print(f"  Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_ip_scan())