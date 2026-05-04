import numpy as np
import pandas as pd
import yfinance as yf
from typing import Dict, List
from core.utils.logger import get_data_logger

logger = get_data_logger("MomentumCalculator")


class MomentumCalculator:
    """
    Computes 12-1 month (11-month skip-month) price momentum for a universe of stocks.

    This is the standard academic momentum signal:
        Return = Price(t-21) / Price(t-252) - 1

    where t is today, t-21 is approx. 1 month ago (skip), and t-252 is 12 months ago.
    The 1-month skip avoids short-term reversal contamination.

    Scores are then ranked by percentile within the universe (0.0 = worst, 1.0 = best),
    giving a clean [0, 1] signal for EQRA conviction weighting.
    """

    def __init__(self, lookback_days: int = 252, skip_days: int = 21):
        self.lookback_days = lookback_days  # ~12 months
        self.skip_days = skip_days          # ~1 month skip to avoid reversal

    def _fetch_prices(self, symbols: List[str]) -> pd.DataFrame:
        """
        Fetches ~13 months of daily closing prices via the institutional HistoricalProvider (ArcticDB/Breeze).
        Falls back gracefully per symbol if data is unavailable.
        """
        try:
            from core.data.historical_provider import HistoricalProvider
            provider = HistoricalProvider()
        except Exception as e:
            logger.error(f"MomentumCalculator: Failed to initialize HistoricalProvider ({e}). Returning empty.")
            return pd.DataFrame()
            
        total_days = self.lookback_days + 30 # Request extra buffer
        price_series = {}
        
        for sym in symbols:
            # get_price_series automatically checks ArcticDB first
            series = provider.get_price_series(sym, total_days)
            if not series.empty:
                price_series[sym] = series

        if not price_series:
            logger.warning("MomentumCalculator: All price downloads failed via DB/yfinance. Returning empty.")
            return pd.DataFrame()

        raw = pd.DataFrame(price_series)
        raw = raw.ffill().dropna()

        if isinstance(raw, pd.Series):
            raw = raw.to_frame(name=symbols[0])

        # Strip the .NS suffix from column names
        raw.columns = [c.replace(".NS", "") for c in raw.columns]
        # Keep only symbols that have enough data (at least 85% of lookback window)
        min_obs = int(self.lookback_days * 0.85)
        raw = raw.dropna(axis=1, thresh=min_obs)
        return raw

    def compute_momentum_scores(self, symbols: List[str]) -> Dict[str, float]:
        """
        Main entry point. Returns a dict {symbol: momentum_percentile_rank}.

        For any symbol where price data is unavailable, returns the universe median (0.5).
        This is the neutral score — it neither penalises nor rewards missing data.
        """
        if not symbols:
            return {}

        prices = self._fetch_prices(symbols)

        if prices.empty:
            logger.warning("MomentumCalculator: No price data retrieved. Assigning neutral score 0.5.")
            return {sym: 0.5 for sym in symbols}

        # --- Compute 12-1 month raw momentum ---
        raw_momentum: Dict[str, float] = {}
        for sym in symbols:
            if sym not in prices.columns:
                raw_momentum[sym] = np.nan
                continue

            price_series = prices[sym].dropna()

            if len(price_series) < self.skip_days + 5:
                raw_momentum[sym] = np.nan
                continue

            # t-21 (skip month end) — if fewer than lookback_days of data, use what we have
            t_skip = price_series.iloc[-self.skip_days]

            if len(price_series) >= self.lookback_days:
                t_start = price_series.iloc[-self.lookback_days]
            else:
                t_start = price_series.iloc[0]  # Use earliest available

            if t_start <= 0:
                raw_momentum[sym] = np.nan
                continue

            raw_momentum[sym] = (t_skip / t_start) - 1.0

        # --- Percentile-rank within the screened universe ---
        valid_scores = {s: v for s, v in raw_momentum.items() if not np.isnan(v)}
        all_values = sorted(valid_scores.values())
        n = len(all_values)

        ranked: Dict[str, float] = {}
        for sym in symbols:
            if sym in valid_scores:
                rank = all_values.index(valid_scores[sym])
                ranked[sym] = rank / max(n - 1, 1)   # [0.0, 1.0]
            else:
                ranked[sym] = 0.5   # Neutral for missing data

        logger.info(
            f"MomentumCalculator: Scored {len(valid_scores)}/{len(symbols)} symbols. "
            f"Top: {max(valid_scores, key=valid_scores.get, default='n/a')} "
            f"Bottom: {min(valid_scores, key=valid_scores.get, default='n/a')}"
        )
        return ranked
