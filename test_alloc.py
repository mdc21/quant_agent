import sys
import asyncio
from app.agents.allocator import PathAllocator

async def main():
    allocator = PathAllocator(max_stocks=15, risk_profile="Aggressive", total_capital=1000000)
    print("Running build_equity_sleeve...")
    sleeve = allocator.build_equity_sleeve()
    print(f"Generated {len(sleeve)} positions.")

if __name__ == "__main__":
    asyncio.run(main())
