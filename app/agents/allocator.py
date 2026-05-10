import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Any, Tuple, Optional
from app.agents.eqra import EquityResearchAgent
from app.agents.pfra import PassiveResearchAgent
from app.agents.genpoa import PortfolioArchitect
from core.data.agent_schema import StockCandidate, PassiveVehicle
from sklearn.covariance import LedoitWolf
from core.utils.logger import get_data_logger

logger = get_data_logger("PathAllocator")


_META_CACHE: Dict[str, Tuple[str, str]] = {}

class PathAllocator:
    """
    Path-Asset Allocator — Institutionally constrained, optimizer-driven.

    Pipeline:
      1. Screen stocks via EQRA (QARP + ROA filter)
      2. Fetch 180-day price history → Ledoit-Wolf covariance
      3. Map EQRA conviction scores → Black-Litterman expected returns
      4. Call GENPOA (MVO / HRP fallback) to produce optimal weights
      5. Apply dynamic multi-cap (60/70/80) and risk-based sector caps (15-25%)
      6. Screen passive funds via PFRA and allocate defensive capital equally
    """

    def __init__(
        self,
        max_stocks: int = 15,
        max_funds: int = 5,
        risk_profile: str = "Aggressive",
        total_capital: float = 1_000_000,
        equity_split_percent: int = 60,
        custom_macro_allocation: Optional[float] = None,
        custom_cap_ratios: Optional[Tuple[float, float, float]] = None,
        target_year: int = 2032
    ):
        self.max_stocks = max_stocks
        self.max_funds = max_funds
        self.risk_profile = risk_profile
        
        # 🛡️ Fiduciary Guard: Ensure total_capital is a valid number
        try:
            val = float(total_capital)
            self.total_capital = val if not pd.isna(val) else 1_000_000.0
        except:
            self.total_capital = 1_000_000.0

        try:
            split = float(equity_split_percent) / 100.0
            self.equity_split_percent = split if not pd.isna(split) else 0.6
        except:
            self.equity_split_percent = 0.6
        self.target_year = target_year

        # --- Macro Allocation ---
        if custom_macro_allocation is not None:
            try:
                val = float(custom_macro_allocation)
                self.equity_allocation = val if not pd.isna(val) else 0.60
            except:
                self.equity_allocation = 0.60
        else:
            equity_pct = {"Aggressive": 0.80, "Balanced": 0.60, "Conservative": 0.40}
            self.equity_allocation = equity_pct.get(risk_profile, 0.60)
            
        self.non_equity_allocation = 1.0 - self.equity_allocation

        self.target_equity_capital = self.total_capital * self.equity_allocation
        self.target_defensive_capital = self.total_capital * self.non_equity_allocation

        self.alpha_capital = self.target_equity_capital * self.equity_split_percent
        self.beta_equity_capital = self.target_equity_capital * (1.0 - self.equity_split_percent)

        # --- Base return assumption by risk profile (annualised) ---
        self._base_return = {"Aggressive": 0.15, "Balanced": 0.11, "Moderate": 0.11, "Conservative": 0.08}.get(risk_profile, 0.11)

        # --- Multi-Cap Sieve Targets (Large:Mid:Small) ---
        if custom_cap_ratios is not None and all(not pd.isna(x) for x in custom_cap_ratios):
            self.large_pct, self.mid_pct, self.small_pct = custom_cap_ratios
        else:
            cap_ratios = {
                "Aggressive": (0.60, 0.25, 0.15),
                "Balanced": (0.70, 0.20, 0.10),
                "Conservative": (0.80, 0.15, 0.05)
            }
            self.large_pct, self.mid_pct, self.small_pct = cap_ratios.get(risk_profile, (0.70, 0.20, 0.10))

        self.eqra = EquityResearchAgent()
        self.pfra = PassiveResearchAgent()
        self.genpoa = PortfolioArchitect(
            risk_aversion=2.5,
            max_single_weight=0.08  # RAA §4.2.7 hard constraint
        )

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _fetch_single_metadata(self, symbol: str) -> Tuple[str, str, str]:
        """Fetch metadata for a single symbol (used in parallel pool)."""
        try:
            clean_sym = symbol.strip().lstrip('$')
            from core.utils.symbol_mapper import SymbolMapper
            yahoo_ticker = SymbolMapper.to_yahoo(clean_sym)
            
            # Prefer curated sector mapping
            sector = SymbolMapper.get_sector(clean_sym)
            
            info = yf.Ticker(f"{yahoo_ticker}.NS").info
            if not sector:
                sector = info.get("sector", "Unknown")
            mcap = info.get("marketCap", 0)
            if mcap >= 500_000_000_000:
                cap = "Large Cap"
            elif mcap >= 150_000_000_000:
                cap = "Mid Cap"
            else:
                cap = "Small Cap"
            return symbol, sector, cap
        except Exception:
            return symbol, "Unknown", "Mid Cap"

    def _fetch_metadata_bulk(self, symbols: List[str]) -> dict:
        """Parallelise metadata hydration across all candidates using a thread pool."""
        results = {}
        to_fetch = []
        for s in symbols:
            if s in _META_CACHE:
                logger.info(f"CACHE HIT: Metadata for {s} found in _META_CACHE.")
                results[s] = _META_CACHE[s]
            else:
                to_fetch.append(s)

        if not to_fetch:
            return results

        from concurrent.futures import ThreadPoolExecutor, as_completed
        logger.info(f"PathAllocator: Parallel metadata hydration for {len(to_fetch)} symbols...")
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = {pool.submit(self._fetch_single_metadata, s): s for s in to_fetch}
            for future in as_completed(futures):
                sym, sector, cap = future.result()
                _META_CACHE[sym] = (sector, cap)
                results[sym] = (sector, cap)
        logger.info("PathAllocator: Parallel metadata hydration complete.")
        return results

    def _fetch_price_history(self, symbols: List[str], days: int = 180) -> pd.DataFrame:
        """
        Step 1: Bulk-download price history for all symbols in a single yf.download() call.
        Falls back to sequential ArcticDB reads if bulk download fails.
        Returns a DataFrame of DAILY RETURNS (T × N).
        """
        logger.info(f"PathAllocator: Bulk-fetching {days}-day price history for {len(symbols)} symbols...")
        
        from core.utils.symbol_mapper import SymbolMapper
        # Build Yahoo tickers for bulk download
        ticker_map = {}  # yahoo_ticker -> original_symbol
        for sym in symbols:
            yt = SymbolMapper.to_yahoo(sym.strip().lstrip('$'))
            ticker_map[f"{yt}.NS"] = sym

        yf_tickers = list(ticker_map.keys())
        
        try:
            raw = yf.download(
                yf_tickers,
                period=f"{days}d",
                interval="1d",
                progress=False,
                group_by="ticker",
                auto_adjust=True,
                threads=True
            )
            # Extract Close prices — handle single vs multi-ticker layout
            if isinstance(raw.columns, pd.MultiIndex):
                close = raw.xs("Close", axis=1, level=1)
            else:
                close = raw[["Close"]].rename(columns={"Close": yf_tickers[0]})

            # Rename back to original symbols
            close = close.rename(columns={yt: ticker_map[yt] for yt in yf_tickers if yt in close.columns})

        except Exception as e:
            logger.warning(f"PathAllocator: Bulk download failed ({e}). Falling back to sequential ArcticDB reads...")
            from core.data.historical_provider import HistoricalProvider
            provider = HistoricalProvider()
            price_series = {}
            for sym in symbols:
                series = provider.get_price_series(sym, days)
                if not series.empty:
                    price_series[sym] = series
            if not price_series:
                return pd.DataFrame()
            close = pd.DataFrame(price_series)

        close = close.ffill()
        threshold = int(days * 0.8)
        close = close.dropna(axis=1, thresh=threshold)

        if close.empty:
            return pd.DataFrame()

        returns = close.pct_change().dropna()
        logger.info(f"PathAllocator: Price history ready — {len(returns)} days, {len(returns.columns)} symbols.")
        return returns

    def _build_expected_returns(
        self, symbols: List[str], conviction_map: Dict[str, float]
    ) -> pd.Series:
        """
        Step 2: Convert EQRA conviction scores to expected annual returns.
        Conviction 1.0 → base_return * 1.5 (strong alpha expectation)
        Conviction 0.5 → base_return * 1.0 (market-matching)
        Linear interpolation between these anchors.
        """
        expected = {}
        for sym in symbols:
            conv = conviction_map.get(sym, 0.5)
            # Conviction in [0, 1] → return in [base*0.5, base*1.5]
            exp_ret = self._base_return * (0.5 + conv)
            expected[sym] = exp_ret
        series = pd.Series(expected, name="expected_return")
        logger.info(f"PathAllocator [BL Views]: {series.to_dict()}")
        return series

    def _build_covariance(self, returns: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
        """
        Step 3: Fit Ledoit-Wolf shrunk covariance on 180-day returns.
        Falls back to identity matrix if insufficient data.
        """
        available = [s for s in symbols if s in returns.columns]
        if len(available) < 2:
            logger.warning("PathAllocator: Insufficient price data for LW covariance. Using diagonal identity.")
            n = len(symbols)
            return pd.DataFrame(
                np.eye(n) * 0.04,  # ~20% annualised vol as diagonal
                index=symbols, columns=symbols
            )

        sub_returns = returns[available]
        lw = LedoitWolf()
        lw.fit(sub_returns)
        # Annualise (daily cov → annual cov)
        cov_annual = pd.DataFrame(
            lw.covariance_ * 252,
            index=sub_returns.columns,
            columns=sub_returns.columns
        )
        # Ensure all requested symbols are present
        cov_annual = cov_annual.reindex(index=symbols, columns=symbols).fillna(0)
        logger.info(f"PathAllocator [LW Cov]: Covariance matrix computed ({cov_annual.shape}).")
        return cov_annual

    # ------------------------------------------------------------------
    # PUBLIC SLEEVE BUILDERS
    # ------------------------------------------------------------------

    def build_equity_sleeve(
        self, 
        current_portfolio: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Builds the alpha (direct equity) sleeve using the full optimizer pipeline.
        Now supports rebalancing by accepting a current_portfolio mapping {symbol: weight}.
        """
        logger.info("PathAllocator: Screening entire universe via EQRA...")
        candidates = self.eqra.screen_stocks("ALL")
        if not candidates:
            return []

        # Hydrate sector / cap metadata — PARALLEL (16 threads)
        logger.info(f"PathAllocator: Hydrating metadata for {len(candidates)} candidates in parallel...")
        meta_map = self._fetch_metadata_bulk([c.symbol for c in candidates])
        
        hydrated: List[Dict[str, Any]] = []
        for c in candidates:
            sector, cap = meta_map.get(c.symbol, ("Unknown", "Mid Cap"))
            hydrated.append({
                "symbol": c.symbol,
                "q_score": c.factors.get("q_score", 0),
                "roa": c.factors.get("roa", 0),
                "conviction": c.conviction_score,
                "fiduciary_grade": c.factors.get("fiduciary_grade", False),
                "factors": c.factors,
                "sector": sector,
                "cap": cap,
                "rationale": getattr(c, "rationale", "Fiduciary Candidate")
            })

        # Apply risk-based sector limit (Hard Ceiling)
        sector_cap_pct = {"Aggressive": 0.25, "Balanced": 0.20, "Conservative": 0.15}
        sector_limit = sector_cap_pct.get(self.risk_profile, 0.20)
        
        # Multi-Cap Strict Targets (Capital Weights)
        cap_targets = {
            "Large Cap": self.large_pct,
            "Mid Cap": self.mid_pct,
            "Small Cap": self.small_pct
        }

        # --- SELECTION PHASE (Strategic Sieve) ---
        # 1. Congestion Check with Elite Exemption
        ELITE_COMPOUNDERS = ["HDFCBANK", "ICICIBANK", "RELIANCE", "TCS", "INFY", "TITAN", "ASIANPAINT", "KOTAKBANK"]
        NIFTY50_GIANTS = ["ITC", "AXISBANK", "SBIN", "BHARTIARTL", "LTIM", "HINDUNILVR", "LT"]
        
        for c in hydrated:
            if c["symbol"] in ELITE_COMPOUNDERS:
                # 0% Penalty: We want these even if they overlap
                c["rationale"] += " | Elite Compounder Exemption Applied"
            elif c["symbol"] in NIFTY50_GIANTS:
                # 10% Mild Penalty: Acknowledge overlap but prioritize quality
                c["conviction"] *= 0.90
                c["rationale"] += " | Strategic Overlap Adj (-10%)"

        # 2. Financials Priority (Growth Anchor)
        has_fin = any(c["sector"] == "Financial Services" for c in hydrated[:self.max_stocks])
        if not has_fin:
            top_fin = next((c for c in hydrated if c["sector"] == "Financial Services"), None)
            if top_fin:
                logger.info(f"PathAllocator: Injecting Financial anchor: {top_fin['symbol']}")
                hydrated.insert(0, top_fin)

        n_large = max(1, int(self.max_stocks * self.large_pct))
        n_mid   = max(1, int(self.max_stocks * self.mid_pct))
        n_small = max(1, self.max_stocks - n_large - n_mid)
        
        pool_large = [c for c in hydrated if c["cap"] == "Large Cap"][:n_large]
        pool_mid   = [c for c in hydrated if c["cap"] == "Mid Cap"][:n_mid]
        pool_small = [c for c in hydrated if c["cap"] == "Small Cap"][:n_small]
        
        selected_pool = []
        seen_syms = set()
        for c in pool_large + pool_mid + pool_small:
            if c["symbol"] not in seen_syms:
                selected_pool.append(c)
                seen_syms.add(c["symbol"])
        
        if not selected_pool:
            return []

        symbols = [s["symbol"] for s in selected_pool]
        conviction_map = {s["symbol"]: s["conviction"] for s in selected_pool}
        sector_map = {s["symbol"]: s["sector"] for s in selected_pool}
        cap_map = {s["symbol"]: s["cap"] for s in selected_pool}
        adv_data = {s["symbol"]: s.get("factors", {}).get("adv", 1e9) for s in selected_pool}

        # --- OPTIMIZATION PHASE (Capital-Weight Constraints) ---
        returns_df = self._fetch_price_history(symbols)
        # Apply strict 5% absolute portfolio cap (approx 14% of the alpha sleeve)
        position_cap = 0.05 / self.equity_split_percent if self.equity_split_percent > 0 else 0.15
        
        expected_returns = self._build_expected_returns(symbols, conviction_map)
        cov_matrix = self._build_covariance(returns_df, symbols)

        curr_w = np.zeros(len(symbols))
        if current_portfolio:
            for i, sym in enumerate(symbols):
                curr_w[i] = current_portfolio.get(sym, 0.0)

        # --- DYNAMIC SECTOR VOLATILITY (BETA) OVERLAYS ---
        sector_caps = {}
        sector_floors = {}
        if not returns_df.empty:
            market_returns = returns_df.mean(axis=1)
            market_var = market_returns.var() * 252 # Proxy for market var
            if market_var > 0:
                sector_betas = {}
                unique_sectors = set(sector_map.values())
                for sect in unique_sectors:
                    sect_syms = [s for s in symbols if sector_map.get(s) == sect and s in returns_df.columns]
                    if sect_syms:
                        sect_returns = returns_df[sect_syms].mean(axis=1)
                        cov = np.cov(sect_returns, market_returns)[0, 1] * 252
                        beta = cov / market_var
                        sector_betas[sect] = beta
                
                for sect, beta in sector_betas.items():
                    if beta > 1.25 or sect in ["Metals", "Industrials"]:
                        # Strict cyclical cap for metals/industrials
                        sector_caps[sect] = 0.12
                        logger.info(f"PathAllocator: Cyclical Cap (12%) applied to {sect} (Beta={beta:.2f}).")
                    elif beta > 1.2 and sect == "Financial Services":
                        # Relaxed cap for Financials as they are a strategic anchor
                        sector_caps[sect] = 0.25
                        logger.info(f"PathAllocator: Strategic Financials Cap (25%) applied (Beta={beta:.2f}).")
                    elif beta < 0.8:
                        # Low Volatility: Anchor Floor to 5%
                        sector_floors[sect] = 0.05
                        logger.info(f"PathAllocator [Risk Overlay]: {sect} flagged as LOW VOLATILITY (Beta={beta:.2f}). Anchoring floor at 5%.")

        logger.info(f"PathAllocator: Optimizing {len(symbols)} stocks for {self.risk_profile} (60:25:15 Capital Mandate)...")
        weight_dict, method = self.genpoa.optimize_sleeve(
            symbols, 
            expected_returns, 
            cov_matrix, 
            current_weights=curr_w,
            adv_data=adv_data,
            total_capital=self.alpha_capital,
            sector_map=sector_map,
            cap_map=cap_map,
            sector_limit=sector_limit,
            cap_targets=cap_targets,
            sector_caps=sector_caps,
            sector_floors=sector_floors
        )
        
        # Hydrate the final selection
        final_selected = []
        for s in selected_pool:
            sym = s["symbol"]
            weight = weight_dict.get(sym, 0.0)
            
            # 🛡️ Fiduciary Guard: Ensure weight is a valid number
            if pd.isna(weight) or not isinstance(weight, (int, float, np.float64, np.float32)):
                weight = 0.0
                
            s["target_weight"] = float(weight)
            s["target_capital"] = float(self.alpha_capital * weight)
            s["optimizer"] = method
            final_selected.append(s)

        return final_selected, hydrated

    def build_passive_sleeve(self) -> List[Dict[str, Any]]:
        """
        Builds the passive (beta + defensive) sleeve using PFRA.
        Simplified to ensure category uniqueness and strategic weighting.
        """
        logger.info(f"PathAllocator: Fetching Passive Funds via PFRA (Horizon: {self.target_year})...")
        all_equity_funds = self.pfra.screen_funds(None)
        
        # 1. DEDUPLICATE: Ensure only ONE fund per category to avoid overlapping exposure
        seen_categories = set()
        unique_equity_funds = []
        for f in all_equity_funds:
            if f.category not in seen_categories:
                unique_equity_funds.append(f)
                seen_categories.add(f.category)
            if len(unique_equity_funds) >= self.max_funds:
                break

        defensive_funds = self.pfra.screen_defensive_funds(target_year=self.target_year)
        selected: List[Dict[str, Any]] = []

        # 2. STRATEGIC WEIGHTING: Align with 'Cleaner Portfolio' template
        # Nifty 50 (30-40%), Next 50 (20%), Midcap (20%), Factors/Themes (Rest)
        if unique_equity_funds:
            weights = {}
            others = []
        # 2. STRATEGIC WEIGHTING & RISK-BASED SUPPRESSION
        if unique_equity_funds:
            # Mandate: Filter based on Risk Profile
            # Aggressive: All
            # Balanced: Suppress Midcap & Thematic
            # Conservative: Suppress Next 50, Midcap & Thematic
            
            filtered_funds = []
            for f in unique_equity_funds:
                cat = f.category.lower()
                is_mid = "midcap" in cat
                is_thematic = "manufacturing" in cat or "smallcap" in cat
                is_next = "next_50" in cat
                
                if self.risk_profile == "Aggressive":
                    filtered_funds.append(f)
                elif self.risk_profile in ["Balanced", "Moderate"]:
                    if not (is_mid or is_thematic):
                        filtered_funds.append(f)
                else: # Conservative
                    if not (is_mid or is_thematic or is_next):
                        filtered_funds.append(f)

            if not filtered_funds:
                filtered_funds = unique_equity_funds[:1] # Safety fallback

            weights = {}
            others = []
            for f in filtered_funds:
                cat = f.category.lower()
                if "nifty_50" in cat:
                    weights[f.ticker] = 0.35 # Core
                elif "value" in cat:
                    weights[f.ticker] = 0.15 # Value Factor
                elif "next_50" in cat:
                    weights[f.ticker] = 0.15 # Junior Core
                # Note: Midcap/Thematic suppressed to fulfill the 35/15/15 mandate
            
            # Normalize to 100% of the Beta Equity sleeve (Total 65% of portfolio)
            final_total = sum(weights.values())
            if final_total == 0:
                # If no strategic match, use everything equally as emergency fallback
                weights = {f.ticker: 1.0/len(filtered_funds) for f in filtered_funds}
            else:
                weights = {t: w/final_total for t, w in weights.items()}

            for f in filtered_funds:
                if f.ticker not in weights:
                    continue # Skip unrecognized funds to avoid duplicates
                
                w = weights[f.ticker]
                capital = float(self.beta_equity_capital * w)
                target_w = float(capital / self.total_capital) if self.total_capital > 0 else 0.0
                
                if pd.isna(capital): capital = 0.0
                if pd.isna(target_w): target_w = 0.0

                selected.append({
                    "ticker": f.ticker,
                    "name": f.name,
                    "category": f.category,
                    "tracking_error": getattr(f, "tracking_error", 0),
                    "expense_ratio": getattr(f, "expense_ratio", 0),
                    "conviction": getattr(f, "conviction_score", 0),
                    "target_capital": capital,
                    "target_weight": target_w,
                    "rationale": f"High-conviction {f.category} ({w*100:.0f}% of beta).",
                })

        # 3. DEFENSIVE: Gold, Bonds & Liquid (User's Precision Template)
        if defensive_funds:
            # Mandate: 15% Bonds, 12% Gold, 8% Liquid (Total 35% of portfolio)
            # Internal split of the defensive sleeve (which is 35% of total capital):
            # 15/35 = 43% for Bonds
            # 12/35 = 34% for Gold
            # 8/35  = 23% for Liquid
            gold_fund = next((f for f in defensive_funds if "Gold" in f.name), None)
            liquid_fund = next((f for f in defensive_funds if "Liquid" in f.name), None)
            bond_fund = next((f for f in defensive_funds if "Bharat" in f.name or "TargetMaturity" in f.category), None)
            
            def_configs = [
                (bond_fund, 0.43),   # 15% of total
                (gold_fund, 0.34),   # 12% of total
                (liquid_fund, 0.23)  # 8% of total
            ]
            
            for fund, w in def_configs:
                if fund:
                    capital = float(self.target_defensive_capital * w)
                    target_w = float(capital / self.total_capital) if self.total_capital > 0 else 0.0

                    if pd.isna(capital): capital = 0.0
                    if pd.isna(target_w): target_w = 0.0

                    selected.append({
                        "ticker": fund.ticker,
                        "name": fund.name,
                        "category": fund.category,
                        "tracking_error": getattr(fund, "tracking_error", 0),
                        "expense_ratio": getattr(fund, "expense_ratio", 0),
                        "conviction": getattr(fund, "conviction_score", 0),
                        "target_capital": capital,
                        "target_weight": target_w,
                        "rationale": "Strategic defensive anchor.",
                    })

        return selected
