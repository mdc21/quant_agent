import pandas as pd
import requests
import io
from typing import List

class UniverseFetcher:
    """
    Fetches the official index constituents directly from NSE Archives.
    """
    URLS = {
        "NIFTY 50": "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
        "NIFTY NEXT 50": "https://nsearchives.nseindia.com/content/indices/ind_niftynext50list.csv",
        "NIFTY MIDCAP 100": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
        "NIFTY SMALLCAP 100": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
        "NIFTY SMALLCAP 250": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
        "TEST BATCH": None # Handled internally
    }

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

    def get_universe(self, index_name: str) -> List[str]:
        """Returns a list of symbols for the given index."""
        if index_name == "TEST BATCH":
            return ["RELIANCE", "TCS", "HDFCBANK"]
            
        url = self.URLS.get(index_name.upper())
        if not url:
            print(f"UniverseFetcher: Unknown index {index_name}")
            return []
            
        try:
            print(f"UniverseFetcher: Downloading {index_name} constituents...")
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                if 'Symbol' in df.columns:
                    symbols = df['Symbol'].tolist()
                    print(f"UniverseFetcher: Successfully loaded {len(symbols)} symbols for {index_name}.")
                    return symbols
                else:
                    print(f"UniverseFetcher: 'Symbol' column missing in {index_name} CSV.")
                    return []
            else:
                print(f"UniverseFetcher: Failed to fetch {index_name} (HTTP {response.status_code})")
                return []
        except Exception as e:
            print(f"UniverseFetcher: Error downloading {index_name} ({e})")
            return []
