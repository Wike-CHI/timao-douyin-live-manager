import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test():
    logger.info("Test starting...")
    await asyncio.sleep(1)
    logger.info("Test complete!")
    return True

if __name__ == "__main__":
    logger.info("Running test...")
    result = asyncio.run(test())
    logger.info(f"Result: {result}")
    print("DONE")
