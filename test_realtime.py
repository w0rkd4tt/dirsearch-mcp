#!/usr/bin/env python3
"""Test real-time progress display"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.cli.interactive_menu import InteractiveMenu
from src.config.settings import Settings

async def main():
    settings = Settings()
    menu = InteractiveMenu()
    menu.settings = settings
    await menu._async_run()

if __name__ == "__main__":
    asyncio.run(main())