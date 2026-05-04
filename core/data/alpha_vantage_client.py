import os
import sqlite3
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

class AlphaVantageClient:
    def __init__(self, db_path="app/data/fundamentals.db"):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            print("WARNING: ALPHA_VANTAGE_API_KEY not found in .env")
        self.base_url = "https://www.alphavantage.co/query"
        self.db_path = db_path
        self._init_db()

        # Map ICICI symbols to Alpha Vantage BSE symbols
        self.symbol_map = {
            "RELIANCE": "RELIANCE.BSE",
            "RELIND": "RELIANCE.BSE",
            "TCS": "TCS.BSE",
            "HDFCBANK": "HDFCBANK.BSE",
            "INFY": "INFY.BSE",
            "TATAMOTORS": "TATAMOTORS.BSE",
        }

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_cache (
                symbol TEXT,
                function TEXT,
                data TEXT,
                last_updated REAL,
                PRIMARY KEY (symbol, function)
            )
        """)
        conn.commit()
        conn.close()

    def _fetch_from_api(self, function: str, symbol: str) -> dict:
        av_symbol = self.symbol_map.get(symbol, f"{symbol}.BSE")
        
        # Check cache first (valid for 7 days)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT data, last_updated FROM fundamental_cache WHERE symbol=? AND function=?", (av_symbol, function))
        row = cursor.fetchone()
        
        if row:
            data, last_updated = row
            if time.time() - last_updated < 7 * 24 * 3600:
                conn.close()
                return json.loads(data)
                
        # If not in cache or expired, fetch from API
        print(f"Alpha Vantage: Fetching {function} for {av_symbol}...")
        params = {
            "function": function,
            "symbol": av_symbol,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
        except Exception as e:
            print(f"Alpha Vantage Request Failed: {e}")
            conn.close()
            return {}
        if response.status_code == 200:
            data = response.json()
            
            # Check for rate limits
            if "Note" in data and "rate limit" in data["Note"].lower():
                print(f"Alpha Vantage Rate Limit Hit: {data['Note']}")
                conn.close()
                return {}
                
            if "Information" in data and "rate limit" in data["Information"].lower():
                 print(f"Alpha Vantage Rate Limit Hit: {data['Information']}")
                 conn.close()
                 return {}

            # Cache the result
            cursor.execute("""
                INSERT OR REPLACE INTO fundamental_cache (symbol, function, data, last_updated)
                VALUES (?, ?, ?, ?)
            """, (av_symbol, function, json.dumps(data), time.time()))
            conn.commit()
            conn.close()
            
            # Sleep briefly to avoid tripping the 5 calls/minute free tier limit
            time.sleep(12) 
            return data
        
        conn.close()
        return {}

    def get_fundamentals(self, symbol: str) -> dict:
        """
        Fetches Income Statement, Balance Sheet, and Cash Flow.
        Extracts metrics needed for the EquityResearchAgent.
        """
        income_stmt = self._fetch_from_api("INCOME_STATEMENT", symbol)
        balance_sheet = self._fetch_from_api("BALANCE_SHEET", symbol)
        cash_flow = self._fetch_from_api("CASH_FLOW", symbol)

        if not income_stmt or not balance_sheet or not cash_flow:
            return {}

        try:
            # Alpha Vantage returns annual reports under "annualReports"
            inc_annual = income_stmt.get("annualReports", [])
            bs_annual = balance_sheet.get("annualReports", [])
            cf_annual = cash_flow.get("annualReports", [])

            if len(inc_annual) < 2 or len(bs_annual) < 2 or len(cf_annual) < 2:
                 return {}

            inc_curr = inc_annual[0]
            inc_prev = inc_annual[1]
            
            bs_curr = bs_annual[0]
            bs_prev = bs_annual[1]
            
            cf_curr = cf_annual[0]
            
            # Safely parse floats
            def safe_float(val):
                try:
                    return float(val) if val and val != "None" else 0.0
                except ValueError:
                    return 0.0

            net_income = safe_float(inc_curr.get("netIncome"))
            net_income_prev = safe_float(inc_prev.get("netIncome"))
            
            total_assets = safe_float(bs_curr.get("totalAssets"))
            total_assets_prev = safe_float(bs_prev.get("totalAssets"))
            
            cfo = safe_float(cf_curr.get("operatingCashflow"))
            
            total_liab = safe_float(bs_curr.get("totalLiabilities"))
            total_liab_prev = safe_float(bs_prev.get("totalLiabilities"))
            
            total_equity = safe_float(bs_curr.get("totalShareholderEquity"))
            total_equity_prev = safe_float(bs_prev.get("totalShareholderEquity"))
            
            current_assets = safe_float(bs_curr.get("totalCurrentAssets"))
            current_assets_prev = safe_float(bs_prev.get("totalCurrentAssets"))
            
            current_liab = safe_float(bs_curr.get("totalCurrentLiabilities"))
            current_liab_prev = safe_float(bs_prev.get("totalCurrentLiabilities"))
            
            shares_out = safe_float(bs_curr.get("commonStockSharesOutstanding"))
            shares_out_prev = safe_float(bs_prev.get("commonStockSharesOutstanding"))
            
            gross_profit = safe_float(inc_curr.get("grossProfit"))
            gross_profit_prev = safe_float(inc_prev.get("grossProfit"))
            
            revenue = safe_float(inc_curr.get("totalRevenue"))
            revenue_prev = safe_float(inc_prev.get("totalRevenue"))
            
            ebit = safe_float(inc_curr.get("ebit"))

            # Calculate Ratios
            roa = net_income / total_assets if total_assets else 0
            roa_prev = net_income_prev / total_assets_prev if total_assets_prev else 0
            
            debt_equity = total_liab / total_equity if total_equity else 0
            debt_equity_prev = total_liab_prev / total_equity_prev if total_equity_prev else 0
            
            current_ratio = current_assets / current_liab if current_liab else 0
            current_ratio_prev = current_assets_prev / current_liab_prev if current_liab_prev else 0
            
            gross_margin = gross_profit / revenue if revenue else 0
            gross_margin_prev = gross_profit_prev / revenue_prev if revenue_prev else 0
            
            asset_turnover = revenue / total_assets if total_assets else 0
            asset_turnover_prev = revenue_prev / total_assets_prev if total_assets_prev else 0
            
            capital_employed = total_assets - current_liab
            roce = ebit / capital_employed if capital_employed else 0

            return {
                "net_income": net_income,
                "roa": roa,
                "roa_prev": roa_prev,
                "cfo": cfo,
                "debt_equity": debt_equity,
                "debt_equity_prev": debt_equity_prev,
                "current_ratio": current_ratio,
                "current_ratio_prev": current_ratio_prev,
                "shares_out": shares_out,
                "shares_out_prev": shares_out_prev,
                "gross_margin": gross_margin,
                "gross_margin_prev": gross_margin_prev,
                "asset_turnover": asset_turnover,
                "asset_turnover_prev": asset_turnover_prev,
                "roce": roce,
                "lineage_id": "AlphaVantage_Live"
            }
        except Exception as e:
            print(f"Error parsing Alpha Vantage data for {symbol}: {e}")
            return {}
