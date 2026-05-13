import asyncio
from tools import get_weather

async def test():
    print("Testing get_weather('London')...")
    result = await get_weather("USA")
    print(result)

if __name__ == "__main__":
    asyncio.run(test())
