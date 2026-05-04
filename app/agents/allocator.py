import pandas as pd
import numpy as np
import yfinance as yf
from typing import List, Dict, Any, Tuple, Optional
from app.agents.eqra import EquityResearchAgent
from app.agents.pfra import PassiveResearchAgent
from app.agents.genpoa import PortfolioArchitect
from core.data.agent_schema import StockCandidate, PassiveVehicle
from sklearn.covariance import LedoitWolf


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
        max_funds: int = 15,
        risk_profile: str = "Aggressive",
        total_capital: float = 1_000_000,
        equity_split_percent: int = 60,
        custom_macro_allocation: Optional[float] = None,
        custom_cap_ratios: Optional[Tuple[float, float, float]] = None,
    ):
        self.max_stocks = max_stocks
        self.max_funds = max_funds
        self.risk_profile = risk_profile
        self.total_capital = total_capital
        self.equity_split_percent = equity_split_percent / 100.0

        # --- Macro Allocation ---
        if custom_macro_allocation is not None:
            self.equity_allocation = custom_macro_allocation
        else:
            equity_pct = {"Aggressive": 0.80, "Balanced": 0.60, "Conservative": 0.40}
            self.equity_allocation = equity_pct.get(risk_profile, 0.60)
            
        self.non_equity_allocation = 1.0 - self.equity_allocation

        self.target_equity_capital = self.total_capital * self.equity_allocation
        self.target_defensive_capital = self.total_capital * self.non_equity_allocation

        self.alpha_capital = self.target_equity_capital * self.equity_split_percent
        self.beta_equity_capital = self.target_equity_capital * (1.0 - self.equity_split_percent)

        # --- Base return assumption by risk profile (annualised) ---
        self._base_return = {"Aggressive": 0.15, "Balanced": 0.11, "Conservative": 0.08}[risk_profile]

        # --- Multi-Cap Sieve Targets (Large:Mid:Small) ---
        if custom_cap_ratios is not None:
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

    def _fetch_metadata(self, symbol: str) -> Tuple[str, str]:
        """Hydrate sector and market-cap category via yfinance."""
        try:
            info = yf.Ticker(f"{symbol}.NS").info
            sector = info.get("sector", "Unknown")
            mcap = info.get("marketCap", 0)
            if mcap >= 500_000_000_000:
                cap = "Large Cap"
            elif mcap >= 150_000_000_000:
                cap = "Mid Cap"
            else:
                cap = "Small Cap"
            return sector, cap
        except Exception:
            return "Unknown", "Mid Cap"

    def _fetch_price_history(self, symbols: List[str], days: int = 180) -> pd.DataFrame:
        """
        Step 1: Download 180-day daily closing prices for each symbol via the institutional ArcticDB pipeline.
        Returns a DataFrame of DAILY RETURNS (T × N), dropping symbols with insufficient history.
        """
        print(f"PathAllocator: Fetching {days}-day price history for {len(symbols)} symbols from Local Database...")
        
        try:
            from core.data.historical_provider import HistoricalProvider
            # Instantiate without breeze token; it will pull from ArcticDB or fallback to yfinance internally
            provider = HistoricalProvider()
            
            price_series = {}
            for sym in symbols:
                # get_price_series automatically checks ArcticDB first
                series = provider.get_price_series(sym, days)
                if not series.empty:
                    price_series[sym] = series
        except Exception as e:
            print(f"PathAllocator: Database/HistoricalProvider connection failed ({e}). Falling back to identity.")
            return pd.DataFrame()

        if not price_series:
            print(f"PathAllocator: All price downloads failed. Falling back to identity covariance.")
            return pd.DataFrame()

        raw = pd.DataFrame(price_series)
        raw = raw.ffill().dropna()

        # Drop columns with > 20% missing data
        threshold = int(days * 0.8)
        raw = raw.dropna(axis=1, thresh=threshold)
        
        if raw.empty:
            return pd.DataFrame()
            
        returns = raw.pct_change().dropna()
        print(f"PathAllocator: DB Price history ready — {len(returns)} days, {len(returns.columns)} symbols.")
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
        print(f"PathAllocator [BL Views]: {series.to_dict()}")
        return series

    def _build_covariance(self, returns: pd.DataFrame, symbols: List[str]) -> pd.DataFrame:
        """
        Step 3: Fit Ledoit-Wolf shrunk covariance on 180-day returns.
        Falls back to identity matrix if insufficient data.
        """
        available = [s for s in symbols if s in returns.columns]
        if len(available) < 2:
            print("PathAllocator: Insufficient price data for LW covariance. Using diagonal identity.")
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
        print(f"PathAllocator [LW Cov]: Covariance matrix computed ({cov_annual.shape}).")
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
        print("PathAllocator: Screening entire universe via EQRA...")
        candidates = self.eqra.screen_stocks("ALL")
        if not candidates:
            return []

        # Hydrate sector / cap metadata
        print(f"PathAllocator: Hydrating metadata for {len(candidates)} candidates...")
        hydrated: List[Dict[str, Any]] = []
        for c in candidates:
            sector, cap = self._fetch_metadata(c.symbol)
            hydrated.append({
                "symbol": c.symbol,
                "q_score": c.factors.get("q_score", 0),
                "roa": c.factors.get("roa", 0),
                "conviction": c.conviction_score,
                "fiduciary_grade": c.factors.get("fiduciary_grade", False),
                "factors": c.factors,
                "sector": sector,
                "cap": cap,
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

        # --- SELECTION PHASE (Target-Count Sieve) ---
        # Calculate how many stocks from each category we need to reach max_stocks
        # while roughly matching the capital distribution.
        n_large = max(1, int(self.max_stocks * self.large_pct))
        n_mid   = max(1, int(self.max_stocks * self.mid_pct))
        n_small = max(1, self.max_stocks - n_large - n_mid)
        
        pool_large = [c for c in hydrated if c["cap"] == "Large Cap"][:n_large]
        pool_mid   = [c for c in hydrated if c["cap"] == "Mid Cap"][:n_mid]
        pool_small = [c for c in hydrated if c["cap"] == "Small Cap"][:n_small]
        
        selected_pool = pool_large + pool_mid + pool_small
        
        if not selected_pool:
            return []

        symbols = [s["symbol"] for s in selected_pool]
        conviction_map = {s["symbol"]: s["conviction"] for s in selected_pool}
        sector_map = {s["symbol"]: s["sector"] for s in selected_pool}
        cap_map = {s["symbol"]: s["cap"] for s in selected_pool}
        adv_data = {s["symbol"]: s.get("factors", {}).get("adv", 1e9) for s in selected_pool}

        # --- OPTIMIZATION PHASE (Capital-Weight Constraints) ---
        returns_df = self._fetch_price_history(symbols)
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
                    if beta > 1.2:
                        # High Volatility: Suppress Cap to 12%
                        sector_caps[sect] = 0.12
                        print(f"PathAllocator [Risk Overlay]: {sect} flagged as HIGH VOLATILITY (Beta={beta:.2f}). Capping at 12%.")
                    elif beta < 0.8:
                        # Low Volatility: Anchor Floor to 5%
                        sector_floors[sect] = 0.05
                        print(f"PathAllocator [Risk Overlay]: {sect} flagged as LOW VOLATILITY (Beta={beta:.2f}). Anchoring floor at 5%.")

        print(f"PathAllocator: Optimizing {len(symbols)} stocks for {self.risk_profile} (60:25:15 Capital Mandate)...")
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
            s["target_weight"] = weight
            s["target_capital"] = self.alpha_capital * weight
            s["optimizer"] = method
            final_selected.append(s)

        return final_selected

    def build_passive_sleeve(self) -> List[Dict[str, Any]]:
        """
        Builds the passive (beta + defensive) sleeve using PFRA.
        Passive equity funds use equal weight within beta_equity_capital.
        Defensive funds use equal weight within target_defensive_capital.
        """
        print("PathAllocator: Fetching Passive Funds via PFRA...")
        # Pass None to trigger the dynamic AMFI Smart-Beta scan
        equity_funds = self.pfra.screen_funds(None)[: self.max_funds]
        defensive_funds = self.pfra.screen_defensive_funds()

        selected: List[Dict[str, Any]] = []

        if equity_funds:
            capital_per = self.beta_equity_capital / len(equity_funds)
            for f in equity_funds:
                selected.append({
                    "ticker": f.ticker,
                    "category": f.category,
                    "tracking_error": getattr(f, "tracking_error", 0),
                    "expense_ratio": getattr(f, "expense_ratio", 0),
                    "conviction": getattr(f, "conviction_score", 0),
                    "target_capital": capital_per,
                    "target_weight": capital_per / self.total_capital,
                    "rationale": "Beta Equity Strategy",
                })

        if defensive_funds:
            capital_per = self.target_defensive_capital / len(defensive_funds)
            for f in defensive_funds:
                selected.append({
                    "ticker": f.ticker,
                    "category": f.category,
                    "tracking_error": getattr(f, "tracking_error", 0),
                    "expense_ratio": getattr(f, "expense_ratio", 0),
                    "conviction": getattr(f, "conviction_score", 0),
                    "target_capital": capital_per,
                    "target_weight": capital_per / self.total_capital,
                    "rationale": getattr(f, "rationale", "Defensive Sleeve"),
                })

        return selected
