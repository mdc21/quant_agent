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
      5. Apply 70:20:10 multi-cap and 25% sector caps as hard constraints
      6. Screen passive funds via PFRA and allocate defensive capital equally
    """

    def __init__(
        self,
        max_stocks: int = 15,
        max_funds: int = 15,
        risk_profile: str = "Aggressive",
        total_capital: float = 1_000_000,
        equity_split_percent: int = 60,
    ):
        self.max_stocks = max_stocks
        self.max_funds = max_funds
        self.risk_profile = risk_profile
        self.total_capital = total_capital
        self.equity_split_percent = equity_split_percent / 100.0

        # --- Macro Allocation ---
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
        Step 1: Download 180-day daily closing prices for each symbol.
        Returns a DataFrame of DAILY RETURNS (T × N), dropping symbols
        with insufficient history.
        """
        print(f"PathAllocator: Fetching {days}-day price history for {len(symbols)} symbols...")
        tickers = [f"{s}.NS" for s in symbols]
        try:
            raw = yf.download(
                tickers,
                period=f"{days}d",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )["Close"]
        except Exception as e:
            print(f"PathAllocator: Price download failed ({e}). Falling back to identity covariance.")
            return pd.DataFrame()

        if isinstance(raw, pd.Series):
            raw = raw.to_frame(name=symbols[0])

        # Rename columns back to plain symbols
        raw.columns = [c.replace(".NS", "") for c in raw.columns]

        # Drop columns with > 20% missing data
        threshold = int(days * 0.8)
        raw = raw.dropna(axis=1, thresh=threshold)
        returns = raw.pct_change().dropna()
        print(f"PathAllocator: Price history ready — {len(returns)} days, {len(returns.columns)} symbols.")
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

        # Apply risk-based multi-cap constraint and 25% sector cap
        target_large = max(1, int(self.max_stocks * self.large_pct))
        target_mid   = max(1, int(self.max_stocks * self.mid_pct))
        target_small = max(1, int(self.max_stocks * self.small_pct))
        while target_large + target_mid + target_small > self.max_stocks:
            target_large -= 1
        while target_large + target_mid + target_small < self.max_stocks:
            target_large += 1

        # --- Dynamic Sector Guardrails ---
        sector_momentum = {}
        for c in hydrated:
            s = c["sector"]
            if s not in sector_momentum: sector_momentum[s] = []
            sector_momentum[s].append(c.get("factors", {}).get("momentum", 0.5))
        
        avg_sector_mom = {s: np.mean(m) for s, m in sector_momentum.items()}
        
        counts = {"Large Cap": 0, "Mid Cap": 0, "Small Cap": 0}
        targets = {"Large Cap": target_large, "Mid Cap": target_mid, "Small Cap": target_small}
        sector_counts: Dict[str, int] = {}
        selected: List[Dict[str, Any]] = []

        for c in hydrated:
            if len(selected) >= self.max_stocks:
                break
            cap, sector = c["cap"], c["sector"]
            
            # Base cap is 15% of max stocks (Consistently Diversified)
            # Healthy Ceiling is 20% (Institutional Standard)
            base_sector_cap = max(1, int(self.max_stocks * 0.15))
            
            # Adjust based on sector momentum, but capped at 20% absolute
            mom = avg_sector_mom.get(sector, 0.5)
            if mom > 0.7: 
                adjusted_cap = max(1, int(self.max_stocks * 0.20)) # Hard Ceiling at 20%
            elif mom < 0.3: 
                adjusted_cap = max(1, int(self.max_stocks * 0.10)) # Defensive Floor at 10%
            else: 
                adjusted_cap = base_sector_cap
            
            if counts.get(cap, 0) < targets.get(cap, 0):
                if sector_counts.get(sector, 0) < adjusted_cap:
                    selected.append(c)
                    counts[cap] = counts.get(cap, 0) + 1
                    sector_counts[sector] = sector_counts.get(sector, 0) + 1

        if not selected:
            return []

        symbols = [s["symbol"] for s in selected]
        conviction_map = {s["symbol"]: s["conviction"] for s in selected}
        
        # Extract ADV data from factors if available
        adv_data = {s["symbol"]: s.get("factors", {}).get("adv", 1e9) for s in selected}

        # --- Step 1: Price history ---
        returns_df = self._fetch_price_history(symbols)

        # --- Step 2: Expected returns from EQRA conviction ---
        expected_returns = self._build_expected_returns(symbols, conviction_map)

        # --- Step 3: Ledoit-Wolf covariance ---
        cov_matrix = self._build_covariance(returns_df, symbols)

        # --- Step 4: Rebalancing Weights ---
        # Map current_portfolio to the symbols list
        curr_w = np.zeros(len(symbols))
        if current_portfolio:
            for i, sym in enumerate(symbols):
                curr_w[i] = current_portfolio.get(sym, 0.0)

        # --- Step 5: GENPOA optimization (MVO → HRP fallback) ---
        print("PathAllocator: Calling GENPOA with Dynamic TCM...")
        weight_dict, method = self.genpoa.optimize_sleeve(
            symbols, 
            expected_returns, 
            cov_matrix, 
            current_weights=curr_w,
            adv_data=adv_data,
            total_capital=self.alpha_capital
        )
        print(f"PathAllocator: Optimization complete via [{method}].")

        # Assign final capital and weights
        # weight_dict values are fractions of the equity sleeve (sum to 1)
        total_sleeve_weight = sum(weight_dict.values())
        for c in selected:
            sleeve_frac = weight_dict.get(c["symbol"], 1.0 / len(selected))
            if total_sleeve_weight > 0:
                sleeve_frac /= total_sleeve_weight  # Re-normalise to 1.0
            c["target_capital"] = self.alpha_capital * sleeve_frac
            c["target_weight"] = c["target_capital"] / self.total_capital
            c["optimizer"] = method

        return selected

    def build_passive_sleeve(self) -> List[Dict[str, Any]]:
        """
        Builds the passive (beta + defensive) sleeve using PFRA.
        Passive equity funds use equal weight within beta_equity_capital.
        Defensive funds use equal weight within target_defensive_capital.
        """
        print("PathAllocator: Fetching Passive Funds via PFRA...")
        scheme_codes = ["120586", "103504", "147701", "120594"]
        equity_funds = self.pfra.screen_funds(scheme_codes)[: self.max_funds]
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
