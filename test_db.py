import sys
import logging
from core.data.historical_provider import HistoricalProvider

# Configure logging to see info messages
logging.basicConfig(level=logging.INFO)

def main():
    provider = HistoricalProvider()
    print("Testing a stock ticker: RELIANCE")
    series = provider.get_price_series("RELIANCE", 180)
    print(f"Returned series shape: {series.shape}")
    
    print("\nTesting an index ticker: NIFTY")
    series2 = provider.get_price_series("NIFTY", 180)
    print(f"Returned series shape: {series2.shape}")

if __name__ == "__main__":
    main()
