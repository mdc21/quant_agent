import requests
import pandas as pd
from typing import Tuple, Optional
from core.utils.logger import get_data_logger

logger = get_data_logger("MFApiClient")

class MFApiClient:
    def __init__(self):
        self.base_url = "https://api.mfapi.in/mf"
        self.amfi_url = "https://www.amfiindia.com/spages/NAVAll.txt"

    def _fetch_from_amfi(self, scheme_code: str) -> dict:
        """Fallback text parser for the official AMFI India daily NAV list."""
        logger.warning(f"Falling back to AMFI TextParser for {scheme_code}...")
        try:
            response = requests.get(self.amfi_url, timeout=10)
            if response.status_code == 200:
                # The text file has lines formatted with semicolons:
                # Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
                for line in response.text.split('\n'):
                    parts = line.strip().split(';')
                    if len(parts) >= 6 and parts[0] == scheme_code:
                        scheme_name = parts[3]
                        nav = float(parts[4])
                        date_str = parts[5]
                        
                        logger.info(f"Successfully recovered latest NAV for {scheme_code} from AMFI.")
                        return {
                            "scheme_name": scheme_name,
                            "scheme_code": scheme_code,
                            "latest_nav": nav,
                            "date": date_str,
                            "lineage_id": "AMFI_Fallback"
                        }
        except Exception as e:
            logger.error(f"AMFI Fallback failed for {scheme_code}: {e}")
            
        return {}

    def get_latest_nav(self, scheme_code: str) -> dict:
        """
        Fetches the latest NAV and metadata for a given mutual fund scheme code.
        Example scheme_code for ICICI Pru Midcap Direct Plan Growth: 120586
        """
        url = f"{self.base_url}/{scheme_code}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "SUCCESS":
                    meta = data.get("meta", {})
                    nav_data = data.get("data", [])
                    if nav_data:
                        latest = nav_data[0]
                        return {
                            "scheme_name": meta.get("scheme_name"),
                            "scheme_code": scheme_code,
                            "latest_nav": float(latest.get("nav")),
                            "date": latest.get("date"),
                            "lineage_id": "MFApi_Live"
                        }
        except Exception as e:
            logger.error(f"Error fetching NAV for scheme {scheme_code} from MFAPI: {e}")
            
        # Fallback to AMFI
        return self._fetch_from_amfi(scheme_code)

    def get_historical_navs(self, scheme_code: str) -> Tuple[Optional[str], pd.Series]:
        """
        Returns the scheme name and a Pandas Series of historical NAVs indexed by date.
        """
        url = f"{self.base_url}/{scheme_code}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "SUCCESS":
                    meta = data.get("meta", {})
                    nav_data = data.get("data", [])
                    
                    if not nav_data:
                        return None, pd.Series()
                        
                    df = pd.DataFrame(nav_data)
                    df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')
                    df['nav'] = pd.to_numeric(df['nav'])
                    
                    # Sort chronologically (oldest to newest)
                    df = df.sort_values('date').set_index('date')
                    return meta.get('scheme_name'), df['nav']
        except Exception as e:
            logger.error(f"Error fetching historical NAVs for scheme {scheme_code} from MFAPI: {e}")
        
        # Fallback to AMFI for single latest point
        amfi_data = self._fetch_from_amfi(scheme_code)
        if amfi_data:
            logger.warning(f"Returning single-point historical series from AMFI for {scheme_code}")
            try:
                date_idx = pd.to_datetime([amfi_data['date']], format='%d-%b-%Y')
            except:
                date_idx = pd.to_datetime([amfi_data['date']])
            series = pd.Series([amfi_data['latest_nav']], index=date_idx)
            return amfi_data['scheme_name'], series
            
        return None, pd.Series()
