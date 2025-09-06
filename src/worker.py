import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from investigate_worker import main as investigate_main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Delegate to the investigate worker main entrypoint."""
    await investigate_main()

if __name__ == "__main__":
    asyncio.run(main())