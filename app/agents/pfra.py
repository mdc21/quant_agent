import pandas as pd
import numpy as np
from typing import List, Dict, Any
from core.data.agent_schema import PassiveVehicle
from core.utils.logger import get_data_logger

class PassiveResearchAgent:
    """
    Passive Research Agent (PFRA).
    Ensures beta efficiency through low-cost, low-tracking-error funds.
    Satisfies Task A4 of the Agent Mesh.
    """
    def __init__(self, min_adv: float = 5_000_000): # 50 Lakhs floor
        self.min_adv = min_adv
        self.logger = get_data_logger("PFRA")

    def calculate_tracking_error(self, fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calculates annualized tracking error.
        """
        if fund_returns.empty or benchmark_returns.empty:
            return 1.0 # Max error fallback
            
        diff = fund_returns - benchmark_returns
        return float(diff.std() * np.sqrt(252))

    def evaluate_vehicles(self, vehicle_data: List[Dict[str, Any]]) -> List[PassiveVehicle]:
        """
        Screens and ranks passive vehicles based on TE, TER, and Liquidity.
        """
        results = []
        
        for data in vehicle_data:
            # Stage 1: Liquidity Guardrail
            adv = data.get('adv', 0)
            if adv < self.min_adv:
                continue # Disqualified
                
            # Stage 2: Calculate Tracking Error
            te = self.calculate_tracking_error(data['returns'], data['benchmark_returns'])
            
            # Stage 3: Conviction Scoring (50% TE, 30% TER, 20% Liquidity)
            # Normalize scores (Lower TE/TER is better)
            # Assuming TE max 0.05 (5%) and TER max 0.02 (2%) for normalization
            te_score = max(0, 1 - (te / 0.05))
            ter_score = max(0, 1 - (data['ter'] / 0.02))
            liq_score = data.get('liq_score', 0.5) # 0 to 1 scale
            
            conviction = (0.5 * te_score) + (0.3 * ter_score) + (0.2 * liq_score)
            
            results.append(PassiveVehicle(
                ticker=data['ticker'],
                category=data['category'],
                tracking_error=te,
                expense_ratio=data['ter'],
                liquidity_score=liq_score,
                conviction_score=conviction,
                rationale=f"TE: {te:.2%}, TER: {data['ter']:.2%}, Liquidity: {liq_score:.2f}"
            ))
            
        # Sort by conviction
        return sorted(results, key=lambda x: x.conviction_score, reverse=True)

    def screen_funds(self, scheme_codes: List[str] = None) -> List[PassiveVehicle]:
        """
        Orchestrates live data fetching for Mutual Funds and calculates live Tracking Error.
        """
        from core.data.mfapi_client import MFApiClient
        from core.data.historical_provider import HistoricalProvider
        import datetime
        
        if scheme_codes is None:
            # 120586: ICICI Pru Midcap
            # 103504: SBI Nifty Index Fund
            scheme_codes = ["120586", "103504"]
            
        mf_client = MFApiClient()
        hp = HistoricalProvider()
        
        self.logger.info("Fetching live NIFTY Benchmark returns...")
        try:
            # We try to fetch NIFTY. ICICI Breeze uses "NIFTY" for the index.
            nifty_prices = hp.get_price_series("NIFTY", lookback_days=180)
            if not nifty_prices.empty:
                nifty_returns = nifty_prices.pct_change().dropna()
            else:
                nifty_returns = pd.Series()
        except Exception as e:
            self.logger.warning(f"Failed to fetch NIFTY from Breeze ({e}). Mocking benchmark...")
            nifty_returns = pd.Series()

        # If NIFTY fetch fails, we use yfinance as a robust fallback
        if nifty_returns.empty:
            import yfinance as yf
            self.logger.info("Fetching NIFTY (^NSEI) fallback via YFinance...")
            try:
                nifty_df = yf.download("^NSEI", period="180d", interval="1d", progress=False)
                if not nifty_df.empty:
                    nifty_returns = nifty_df["Close"].pct_change().dropna()
                    if isinstance(nifty_returns, pd.DataFrame):
                        nifty_returns = nifty_returns.iloc[:, 0]
                else:
                    raise ValueError("Empty YFinance download")
            except Exception as ye:
                self.logger.error(f"YFinance fallback failed ({ye}). Using flat zero-return series.")
                # Final fallback to zero returns to avoid crash, but with a warning
                dates = pd.date_range(end=pd.Timestamp.today(), periods=180, freq='B')
                nifty_returns = pd.Series(0.0, index=dates)

        vehicle_data = []
        for code in scheme_codes:
            self.logger.info(f"Fetching live NAVs for scheme {code}...")
            name, navs = mf_client.get_historical_navs(code)
            
            if not navs.empty:
                fund_returns = navs.pct_change().dropna()
                
                # Align dates for Tracking Error calculation
                aligned_df = pd.concat([fund_returns, nifty_returns], axis=1).dropna()
                aligned_fund = aligned_df.iloc[:, 0]
                aligned_nifty = aligned_df.iloc[:, 1]
                
                # Fetch Live Expense Ratio (TER) via Groww API
                ter = 0.005 # Default 0.5%
                try:
                    import requests
                    search_url = f"https://groww.in/v1/api/search/v1/derived/scheme?available_for_investment=true&doc_type=scheme&q={name}&size=1"
                    headers = {"User-Agent": "Mozilla/5.0"}
                    res = requests.get(search_url, headers=headers, timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        if 'content' in data and len(data['content']) > 0:
                            search_id = data['content'][0].get('search_id')
                            # Hit the detail API
                            detail_url = f"https://groww.in/v1/api/data/mf/web/v3/scheme/search/{search_id}"
                            d_res = requests.get(detail_url, headers=headers, timeout=5)
                            if d_res.status_code == 200:
                                d_data = d_res.json()
                                # Groww usually stores expense ratio in 'expense_ratio' or 'ter'
                                ter_val = d_data.get('expense_ratio', d_data.get('ter'))
                                if ter_val is not None:
                                    ter = float(ter_val) / 100.0 # Convert percentage to decimal
                except Exception as e:
                    self.logger.warning(f"Failed to fetch live TER for {name} ({e}). Using default.")
                
                vehicle_data.append({
                    "ticker": name or f"Fund_{code}",
                    "category": "Index/ETF" if name and "Index" in name else "Mutual Fund",
                    "returns": aligned_fund,
                    "benchmark_returns": aligned_nifty,
                    "ter": ter,
                    "adv": 50_000_000, # Mock high liquidity
                    "liq_score": 0.9
                })
            else:
                self.logger.warning(f"No NAV data found for {code}")

        if not vehicle_data:
            self.logger.warning("Failed to fetch live mutual funds. Returning fallback index vehicles.")
            return [
                PassiveVehicle(
                    ticker="NIFTYBEES ETF", category="Index/ETF", tracking_error=0.005,
                    expense_ratio=0.001, liquidity_score=0.95, conviction_score=0.92,
                    rationale="Fallback: Nifty 50 Benchmark"
                ),
                PassiveVehicle(
                    ticker="JUNIORBEES ETF", category="Index/ETF", tracking_error=0.008,
                    expense_ratio=0.0015, liquidity_score=0.90, conviction_score=0.85,
                    rationale="Fallback: Nifty Next 50 Benchmark"
                ),
                PassiveVehicle(
                    ticker="MID150BEES ETF", category="Index/ETF", tracking_error=0.012,
                    expense_ratio=0.002, liquidity_score=0.85, conviction_score=0.80,
                    rationale="Fallback: Midcap 150 Benchmark"
                )
            ]

        return self.evaluate_vehicles(vehicle_data)

    def screen_defensive_funds(self) -> List[PassiveVehicle]:
        """
        Returns Defensive Assets (Debt/Gold) for the Non-Equity portion of the portfolio.
        Attempts to fetch live data to calculate real-time TE.
        """
        defensive_configs = [
            {"ticker": "LIQUIDBEES.NS", "category": "Debt/Liquid", "ter": 0.001, "rationale": "Cash equivalent. Low duration risk."},
            {"ticker": "GOLDBEES.NS", "category": "Commodity", "ter": 0.008, "rationale": "Inflation hedge."},
            {"ticker": "GILTBEES.NS", "category": "Debt/Sovereign", "ter": 0.005, "rationale": "Sovereign safety."}
        ]
        
        import yfinance as yf
        results = []
        
        # We use NIFTY as a broad benchmark even for defensive to see relative protection
        # In a more advanced version, GOLDBEES would benchmark against Gold spot prices.
        dates = pd.date_range(end=pd.Timestamp.today(), periods=180, freq='B')
        nifty_mock = pd.Series(0.0, index=dates) # Neutral benchmark for defensive
        
        for config in defensive_configs:
            try:
                self.logger.info(f"Fetching live data for defensive ETF: {config['ticker']}")
                df = yf.download(config['ticker'], period="180d", interval="1d", progress=False)
                if not df.empty:
                    rets = df["Close"].pct_change().dropna()
                    if isinstance(rets, pd.DataFrame): rets = rets.iloc[:, 0]
                    
                    te = self.calculate_tracking_error(rets, nifty_mock) # Defensive TE vs cash-like
                    
                    results.append(PassiveVehicle(
                        ticker=config['ticker'].replace(".NS", ""),
                        category=config['category'],
                        tracking_error=te,
                        expense_ratio=config['ter'],
                        liquidity_score=0.98,
                        conviction_score=0.90, # High default for defensive mandate
                        rationale=config['rationale']
                    ))
                    continue
            except Exception as e:
                self.logger.warning(f"Failed to fetch live {config['ticker']} ({e}). Using fallback.")
            
            # Fallback if yfinance fails
            results.append(PassiveVehicle(
                ticker=config['ticker'].replace(".NS", ""),
                category=config['category'],
                tracking_error=0.01,
                expense_ratio=config['ter'],
                liquidity_score=0.95,
                conviction_score=0.85,
                rationale=config['rationale'] + " (Fallback Data)"
            ))
            
        return results

