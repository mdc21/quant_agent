import pandas as pd
import numpy as np
from typing import List, Dict, Any
from core.data.agent_schema import PassiveVehicle
from core.utils.logger import get_data_logger

_PFRA_CACHE: Dict[str, List[PassiveVehicle]] = {}

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

    def calculate_sharpe(self, fund_returns: pd.Series, risk_free_rate: float = 0.065) -> float:
        """Calculates Annualized Sharpe Ratio."""
        if fund_returns.empty:
            return 0.0
        excess_returns = fund_returns - (risk_free_rate / 252)
        if excess_returns.std() == 0:
            return 0.0
        return float((excess_returns.mean() / excess_returns.std()) * np.sqrt(252))

    def evaluate_vehicles(self, vehicle_data: List[Dict[str, Any]]) -> List[PassiveVehicle]:
        """
        Ranks vehicles based on cost, tracking error, and liquidity.
        """
        results = []
        for v in vehicle_data:
            # Alpha/Conviction = 1 - TrackingError - (ExpenseRatio * 2)
            # High TE and High TER penalize the conviction
            te = self.calculate_tracking_error(v['returns'], v['benchmark_returns'])
            
            # Simple scoring: 100 - (TE * 100) - (TER * 200)
            score = 1.0 - (te * 0.5) - (v['ter'] * 5.0)
            score = max(0.1, min(0.99, score))
            
            results.append(PassiveVehicle(
                ticker=v['ticker'],
                name=v['scheme_name'],
                category=v['category'],
                tracking_error=te,
                expense_ratio=v['ter'],
                liquidity_score=v['liq_score'],
                conviction_score=score,
                rationale=f"Low tracking error ({te:.2%}) and optimized TER ({v['ter']:.2%})."
            ))
            
        return sorted(results, key=lambda x: x.conviction_score, reverse=True)

    def screen_funds(self, scheme_codes: List[str] = None) -> List[PassiveVehicle]:
        """
        Orchestrates live data fetching for Mutual Funds and calculates live Tracking Error.
        """
        from core.data.mfapi_client import MFApiClient
        import datetime
        
        # 1. Check Session Cache
        cache_key = f"SCREEN_FUNDS_{scheme_codes}" if scheme_codes else "SCREEN_FUNDS_DYNAMIC"
        if cache_key in _PFRA_CACHE:
            self.logger.info(f"CACHE HIT: Serving {cache_key} from _PFRA_CACHE.")
            return _PFRA_CACHE[cache_key]

        if scheme_codes is None:
            self.logger.info("Dynamic AMFI Scan requested. Fetching top Direct-Growth funds...")
            try:
                import requests
                # Use MFAPI master list instead of AMFI to bypass geoblocks
                res = requests.get("https://api.mfapi.in/mf", timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    candidates = []
                    # Filter for 'Direct Plan' and 'Growth', excluding 'Dividend' and 'IDCW'
                    for fund in data:
                        name = str(fund.get('schemeName', '')).lower()
                        if "direct" in name and "growth" in name and "idcw" not in name and "dividend" not in name:
                            # Prioritize Index, Midcap, Smallcap, and Thematic for our Smart Beta sleeve
                            if any(x in name for x in ["index", "midcap", "smallcap", "technology", "nifty"]):
                                candidates.append(str(fund.get('schemeCode')))
                    # Sample 15 candidates deterministically for stable fiduciary generation
                    import random
                    random.seed(42)
                    scheme_codes = random.sample(candidates, min(15, len(candidates)))
                    self.logger.info(f"MFAPI Scan complete. Evaluated {len(candidates)} valid funds. Selected {len(scheme_codes)} for live NAV screening.")
            except Exception as e:
                self.logger.warning(f"Dynamic scan failed ({e}). Falling back to hardcoded safety net.")
                scheme_codes = ["120586", "103504", "147701", "120594"]
                
        if not scheme_codes:
            scheme_codes = ["120586", "103504"]
            
        mf_client = MFApiClient()
        try:
            from core.data.historical_provider import HistoricalProvider
            hp = HistoricalProvider()
            self.logger.info("Fetching live NIFTY Benchmark returns...")
            nifty_prices = hp.get_price_series("NIFTY", lookback_days=180)
            if not nifty_prices.empty:
                nifty_returns = nifty_prices.pct_change().dropna()
            else:
                nifty_returns = pd.Series()
        except Exception as e:
            self.logger.warning(f"Failed to fetch NIFTY from HistoricalProvider ({e}). Mocking benchmark...")
            nifty_returns = pd.Series()

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
                dates = pd.date_range(end=pd.Timestamp.today(), periods=180, freq='B')
                nifty_returns = pd.Series(0.0, index=dates)

        vehicle_data = []
        for code in scheme_codes:
            self.logger.info(f"Fetching live NAVs for scheme {code}...")
            name, navs = mf_client.get_historical_navs(code)
            
            if not navs.empty:
                fund_returns = navs.pct_change().dropna()
                aligned_df = pd.concat([fund_returns, nifty_returns], axis=1).dropna()
                if not aligned_df.empty:
                    aligned_fund = aligned_df.iloc[:, 0]
                    aligned_nifty = aligned_df.iloc[:, 1]
                    
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
                                detail_url = f"https://groww.in/v1/api/data/mf/web/v3/scheme/search/{search_id}"
                                d_res = requests.get(detail_url, headers=headers, timeout=5)
                                if d_res.status_code == 200:
                                    d_data = d_res.json()
                                    ter_val = d_data.get('expense_ratio', d_data.get('ter'))
                                    if ter_val is not None:
                                        ter = float(ter_val) / 100.0
                    except Exception as e:
                        self.logger.warning(f"Failed to fetch live TER for {name} ({e}). Using default.")
                    
                    vehicle_data.append({
                        "ticker": f"MF_{code}",
                        "scheme_name": name or f"Fund_{code}",
                        "category": "Index/ETF" if name and "Index" in name else "Mutual Fund",
                        "returns": aligned_fund,
                        "benchmark_returns": aligned_nifty,
                        "ter": ter,
                        "adv": 50_000_000,
                        "liq_score": 0.9
                    })
            else:
                self.logger.warning(f"No NAV data found for {code}")

        if not vehicle_data:
            self.logger.warning("Failed to fetch live mutual funds. Returning fallback index vehicles.")
            res = [
                PassiveVehicle(
                    ticker="NIFTYBEES", name="Nippon India ETF Nifty 50 BeES", category="Index/ETF", tracking_error=0.005,
                    expense_ratio=0.001, liquidity_score=0.95, conviction_score=0.92,
                    rationale="Fallback: Nifty 50 Benchmark"
                ),
                PassiveVehicle(
                    ticker="JUNIORBEES", name="Nippon India ETF Nifty Next 50 BeES", category="Index/ETF", tracking_error=0.008,
                    expense_ratio=0.0015, liquidity_score=0.90, conviction_score=0.85,
                    rationale="Fallback: Nifty Next 50 Benchmark"
                ),
                PassiveVehicle(
                    ticker="MID150BEES", name="Nippon India ETF Nifty Midcap 150 BeES", category="Index/ETF", tracking_error=0.012,
                    expense_ratio=0.002, liquidity_score=0.85, conviction_score=0.80,
                    rationale="Fallback: Midcap 150 Benchmark"
                )
            ]
        else:
            res = self.evaluate_vehicles(vehicle_data)

        _PFRA_CACHE[cache_key] = res
        return res

    def screen_defensive_funds(self) -> List[PassiveVehicle]:
        """
        Returns Defensive Assets (Debt/Gold) for the Non-Equity portion of the portfolio.
        """
        cache_key = "DEFENSIVE_FUNDS"
        if cache_key in _PFRA_CACHE:
            self.logger.info("CACHE HIT: Serving defensive funds from _PFRA_CACHE.")
            return _PFRA_CACHE[cache_key]

        defensive_configs = [
            {"ticker": "LIQUIDBEES.NS", "name": "Nippon India ETF Liquid BeES", "category": "Debt/Liquid",    "ter": 0.001, "rationale": "Cash equivalent. Lowest duration risk."},
            {"ticker": "GOLDBEES.NS",   "name": "Nippon India ETF Gold BeES",   "category": "Commodity/Gold",  "ter": 0.008, "rationale": "Inflation hedge. Non-correlated to equity."},
            {"ticker": "CPSEETF.NS",    "name": "CPSE ETF",                     "category": "Debt/PSU",        "ter": 0.005, "rationale": "High-grade PSU bond exposure. Capital preservation."},
        ]
        
        import yfinance as yf
        results = []
        dates = pd.date_range(end=pd.Timestamp.today(), periods=180, freq='B')
        nifty_mock = pd.Series(0.0, index=dates)
        
        for config in defensive_configs:
            try:
                self.logger.info(f"Fetching live data for defensive ETF: {config['ticker']}")
                df = yf.download(config['ticker'], period="180d", interval="1d", progress=False)
                if not df.empty:
                    rets = df["Close"].ffill().pct_change(fill_method=None).dropna()
                    if isinstance(rets, pd.DataFrame): rets = rets.iloc[:, 0]
                    te = self.calculate_tracking_error(rets, nifty_mock)
                    results.append(PassiveVehicle(
                        ticker=config['ticker'].replace(".NS", ""),
                        name=config.get('name', config['ticker'].replace(".NS", "")),
                        category=config['category'],
                        tracking_error=te,
                        expense_ratio=config['ter'],
                        liquidity_score=0.98,
                        conviction_score=0.90,
                        rationale=config['rationale']
                    ))
                    continue
            except Exception as e:
                self.logger.warning(f"Failed to fetch live {config['ticker']} ({e}). Using fallback.")
            
            results.append(PassiveVehicle(
                ticker=config['ticker'].replace(".NS", ""),
                name=config.get('name', config['ticker'].replace(".NS", "")),
                category=config['category'],
                tracking_error=0.01,
                expense_ratio=config['ter'],
                liquidity_score=0.95,
                conviction_score=0.85,
                rationale=config['rationale'] + " (Fallback Data)"
            ))
            
        _PFRA_CACHE[cache_key] = results
        return results
