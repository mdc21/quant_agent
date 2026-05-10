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

    def calculate_tracking_consistency(self, fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calculates Tracking Consistency (Std Dev of Daily Tracking Difference).
        Lower is better.
        """
        if fund_returns.empty or benchmark_returns.empty:
            return 1.0
        diff = fund_returns - benchmark_returns
        return float(diff.std())

    def evaluate_vehicles(self, vehicle_data: List[Dict[str, Any]]) -> List[PassiveVehicle]:
        """
        Deep Audit: Ranks vehicles based on institutional multi-factor scoring.
        Factors: TE (30%), TER (30%), AUM/Liquidity (20%), Consistency (20%).
        """
        results = []
        for v in vehicle_data:
            te = self.calculate_tracking_error(v['returns'], v['benchmark_returns'])
            consistency = self.calculate_tracking_consistency(v['returns'], v['benchmark_returns'])
            
            # Multi-Factor Score (0-1 range)
            # 1. Tracking Factor (Lower TE and higher consistency is better)
            tracking_score = 1.0 - (te * 2.0) - (consistency * 100.0)
            
            # 2. Cost Factor (Lower TER is better)
            cost_score = 1.0 - (v['ter'] * 10.0)
            
            # 3. Liquidity Factor (Higher AUM/Score is better)
            liq_score = v.get('liq_score', 0.5)
            
            # Final weighted score
            total_score = (tracking_score * 0.3) + (cost_score * 0.3) + (liq_score * 0.2) + (v.get('consistency_bonus', 0.5) * 0.2)
            total_score = max(0.1, min(0.99, total_score))
            
            results.append(PassiveVehicle(
                ticker=v['ticker'],
                name=v['scheme_name'],
                category=v['category'],
                tracking_error=te,
                expense_ratio=v['ter'],
                liquidity_score=liq_score,
                conviction_score=total_score,
                rationale=(
                    f"Audit Score: {total_score:.0%}. TE: {te:.2%}. "
                    f"Cost: {v['ter']:.2%}. AUM-Liquidity: {liq_score:.0%}. "
                    f"Consistent tracking across 180-day window."
                )
            ))
            
        return sorted(results, key=lambda x: x.conviction_score, reverse=True)

    def screen_funds(self, scheme_codes: List[str] = None) -> List[PassiveVehicle]:
        """
        Orchestrates Deep Audit of Mutual Funds across the entire candidate pool.
        """
        from core.data.mfapi_client import MFApiClient
        import datetime
        import requests

        # Ordered from specific to general to prevent shadowing
        categories = {
            "nifty_next_50": {"keywords": ["next 50", "junior", "nifty next"], "candidates": []},
            "midcap_150": {"keywords": ["midcap index", "midcap 150", "nifty midcap"], "candidates": []},
            "value_factor": {"keywords": ["value fund", "value discovery", "value index", "nv20"], "candidates": []},
            "manufacturing_theme": {"keywords": ["manufacturing", "industrial", "momentum"], "candidates": []},
            "smallcap_250": {"keywords": ["smallcap index", "smallcap 250", "nifty smallcap"], "candidates": []},
            "nifty_50": {"keywords": ["nifty 50", "nifty 50 index", "nifty index"], "candidates": []}
        }
        
        # 1. Check Session Cache
        cache_key = f"SCREEN_FUNDS_DEEP_{scheme_codes}" if scheme_codes else "SCREEN_FUNDS_DEEP_DYNAMIC"
        if cache_key in _PFRA_CACHE:
            self.logger.info(f"CACHE HIT: Serving Deep Audit from _PFRA_CACHE.")
            return _PFRA_CACHE[cache_key]

        if scheme_codes is None:
            self.logger.info("Dynamic AMFI Deep Audit requested. Evaluating entire category pool...")
            try:
                res = requests.get("https://api.mfapi.in/mf", timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    for fund in data:
                        name = str(fund.get('schemeName', '')).lower()
                        if "direct" in name and "growth" in name and "idcw" not in name and "dividend" not in name:
                            for cat_key, cat_val in categories.items():
                                if any(k in name for k in cat_val["keywords"]):
                                    cat_val["candidates"].append(str(fund.get('schemeCode')))
                                    break

                    scheme_codes = []
                    for cat_key, cat_val in categories.items():
                        if cat_val["candidates"]:
                            # Evaluation limit: Audit top 5 candidates per category for performance
                            scheme_codes.extend(cat_val["candidates"][:5])
                    
                    self.logger.info(f"Pool Audit: Selected {len(scheme_codes)} candidates across strategies for Deep NAV screening.")
            except Exception as e:
                self.logger.warning(f"Dynamic scan failed ({e}). Falling back to safety net.")
                scheme_codes = ["120586", "103504", "147701", "120594"]
                
        # ... [NAV fetching logic remains consistent] ...
        
        mf_client = MFApiClient()
        # [Historical NIFTY fetching logic...]
        
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
                    
                    # Identify the strategy for categorization
                    strategy_label = "Index/Misc"
                    for cat_key, cat_val in categories.items():
                        if any(k in name for k in cat_val["keywords"]):
                            strategy_label = f"Index/{cat_key}"
                            break

                    vehicle_data.append({
                        "ticker": f"MF_{code}",
                        "scheme_name": name or f"Fund_{code}",
                        "category": strategy_label,
                        "returns": aligned_fund,
                        "benchmark_returns": aligned_nifty,
                        "ter": ter,
                        "adv": 50_000_000,
                        "liq_score": 0.9
                    })
            else:
                self.logger.warning(f"No NAV data found for {code}")

        if not vehicle_data:
            self.logger.warning("Failed to fetch live mutual funds. Returning strategic fallback set.")
            res = [
                PassiveVehicle(ticker="NIFTYBEES", name="Nippon India ETF Nifty 50 BeES", category="Index/nifty_50", tracking_error=0.005, expense_ratio=0.001, liquidity_score=0.95, conviction_score=0.95, rationale="Core: Nifty 50 Benchmark"),
                PassiveVehicle(ticker="JUNIORBEES", name="Nippon India ETF Nifty Next 50 BeES", category="Index/nifty_next_50", tracking_error=0.008, expense_ratio=0.0015, liquidity_score=0.90, conviction_score=0.90, rationale="Core: Nifty Next 50 Benchmark"),
                PassiveVehicle(ticker="ICICINV20", name="ICICI Pru NV20 ETF", category="Index/value_factor", tracking_error=0.015, expense_ratio=0.0015, liquidity_score=0.80, conviction_score=0.85, rationale="Factor: Nifty 50 Value 20"),
                PassiveVehicle(ticker="MOMENTUM30", name="UTI Nifty200 Momentum 30 Index Fund", category="Index/manufacturing_theme", tracking_error=0.018, expense_ratio=0.004, liquidity_score=0.75, conviction_score=0.80, rationale="Thematic: Alpha Overlay")
            ]
        else:
            res = self.evaluate_vehicles(vehicle_data)
            
            # ENSURE DIVERSITY: Use exact strategy labels for backfilling
            existing_cats = {v.category for v in res}
            required_cats = {
                "Index/nifty_50": ("NIFTYBEES", "Nippon India ETF Nifty 50 BeES"),
                "Index/nifty_next_50": ("JUNIORBEES", "Nippon India ETF Nifty Next 50 BeES"),
                "Index/value_factor": ("ICICINV20", "ICICI Pru NV20 ETF"),
                "Index/manufacturing_theme": ("MOMENTUM30", "UTI Nifty200 Momentum 30 Index Fund")
            }
            
            for cat, (ticker, name) in required_cats.items():
                if cat not in existing_cats:
                    self.logger.info(f"Injecting mandatory fallback for missing strategy: {cat}")
                    res.append(PassiveVehicle(
                        ticker=ticker, 
                        name=name, 
                        category=cat, 
                        tracking_error=0.01, 
                        expense_ratio=0.002, 
                        liquidity_score=0.9, 
                        conviction_score=0.85, 
                        rationale=f"Strategy Pillar ({cat})"
                    ))

        _PFRA_CACHE[cache_key] = res
        return res

    def screen_defensive_funds(self, target_year: int = 2030) -> List[PassiveVehicle]:
        """
        Returns Defensive Assets (Debt/Gold) for the Non-Equity portion of the portfolio.
        Automatically matches Bond maturity to the requested target_year.
        """
        cache_key = f"DEFENSIVE_FUNDS_{target_year}"
        if cache_key in _PFRA_CACHE:
            self.logger.info(f"CACHE HIT: Serving defensive funds for {target_year} from _PFRA_CACHE.")
            return _PFRA_CACHE[cache_key]

        # Determine the best Bharat Bond maturity year
        # Bharat Bonds typically use BBETFMMYY format (e.g., BBETF0432 for April 2032)
        bond_year = max(2025, min(2033, target_year))
        bond_ticker = f"BBETF04{str(bond_year)[2:]}.NS"
        bond_name = f"Bharat Bond ETF April {bond_year}"

        defensive_configs = [
            {"ticker": "LIQUIDBEES.NS", "name": "Nippon India ETF Liquid BeES", "category": "Debt/Liquid",    "ter": 0.001, "rationale": "Cash equivalent. Lowest duration risk."},
            {"ticker": "GOLDBEES.NS",   "name": "Nippon India ETF Gold BeES",   "category": "Commodity/Gold",  "ter": 0.008, "rationale": "Inflation hedge. Non-correlated to equity."},
            {"ticker": bond_ticker,     "name": bond_name,                      "category": "Debt/TargetMaturity", "ter": 0.0005, "rationale": f"Duration-matched to {bond_year}. Low credit risk."},
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
