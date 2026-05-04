import datetime
import pandas as pd
import numpy as np
from typing import List, Tuple
from core.data.breeze_client import BreezeClient
from core.data.store import DataStore
from core.data.ingestion import IngestionEngine

class HistoricalProvider:
    def __init__(self, session_token: str = None):
        self.breeze = BreezeClient.get_instance(session_token)
        self.store = DataStore()
        self.ingestion = IngestionEngine(self.breeze, self.store)

    def _ensure_data_freshness(self, symbols: List[str], lookback_days: int = 180):
        """Ensures ArcticDB has the latest data for the requested symbols."""
        end_date = datetime.datetime.now(datetime.timezone.utc)
        start_date = end_date - datetime.timedelta(days=lookback_days)
        
        from_date_str = start_date.strftime("%Y-%m-%dT00:00:00.000Z")
        to_date_str = end_date.strftime("%Y-%m-%dT23:59:59.000Z")
        
        session_meta = {'lineage_id': f"HIST_{end_date.strftime('%Y%m%d')}"}
        
        available_symbols = self.store.list_symbols()
        
        for sym in symbols:
            # In a production system, we would check if the stored data is fresh.
            # Here we do a simple check: if it's not in ArcticDB at all, ingest it.
            if sym not in available_symbols:
                print(f"HistoricalProvider: {sym} not found in ArcticDB. Fetching live from Breeze...")
                self.ingestion.ingest_historical_to_arctic(sym, from_date_str, to_date_str, session_meta)

    def get_price_series(self, symbol: str, lookback_days: int = 180) -> pd.Series:
        """Returns the raw daily closing price series for a single symbol."""
        from core.utils.logger import get_data_logger
        import yfinance as yf
        logger = get_data_logger("HistoricalProvider")
        
        self._ensure_data_freshness([symbol], lookback_days)
        df = self.store.read_symbol(symbol)
        if not df.empty and 'close' in df.columns:
            daily_close = df['close'].groupby(df.index.date).last()
            daily_close.index = pd.to_datetime(daily_close.index)
            start_date = pd.Timestamp(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=lookback_days)).tz_localize(None)
            return daily_close.loc[daily_close.index >= start_date]
            
        logger.warning(f"Breeze Price Data missing for {symbol}. Falling back to YFinance...")
        yf_symbol = f"{symbol}.NS"
        if symbol == "NIFTY":
            yf_symbol = "^NSEI"
            
        try:
            start_date = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
            ticker = yf.Ticker(yf_symbol)
            history = ticker.history(start=start_date.strftime("%Y-%m-%d"))
            if not history.empty and 'Close' in history.columns:
                logger.info(f"Successfully retrieved YFinance price series for {yf_symbol}")
                series = history['Close']
                series.index = pd.to_datetime(series.index).tz_localize(None)
                return series
        except Exception as e:
            logger.error(f"YFinance fallback failed for {symbol}: {e}")
            
        return pd.Series()

    def get_returns_and_covariance(self, symbols: List[str], lookback_days: int = 180) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Fetches data, aligns it, and computes:
        Returns:
            expected_returns: pd.Series of annualized expected returns.
            cov_matrix: pd.DataFrame of annualized covariance matrix.
        """
        # 1. Ensure data is available
        self._ensure_data_freshness(symbols, lookback_days)
        
        # 2. Build aligned DataFrame of closing prices
        price_series = {}
        for sym in symbols:
            series = self.get_price_series(sym, lookback_days)
            if not series.empty:
                price_series[sym] = series
            else:
                print(f"HistoricalProvider: No data found for {sym} after ingestion attempt.")
                
        if not price_series:
            print("Warning: No valid historical data retrieved. Falling back to mocks.")
            mock_returns = pd.Series([0.15] * len(symbols), index=symbols)
            mock_cov = pd.DataFrame(np.eye(len(symbols)) * 0.04, index=symbols, columns=symbols)
            return mock_returns, mock_cov

        prices_df = pd.DataFrame(price_series)
        prices_df = prices_df.ffill().dropna() # Forward fill missing days, drop initial NaNs

        # 3. Calculate daily returns
        daily_returns = prices_df.pct_change().dropna()
        
        if len(daily_returns) < 5:
            print("Warning: Not enough valid trading days to compute reliable covariance. Falling back to mocks.")
            mock_returns = pd.Series([0.15] * len(symbols), index=symbols)
            mock_cov = pd.DataFrame(np.eye(len(symbols)) * 0.04, index=symbols, columns=symbols)
            return mock_returns, mock_cov

        # 4. Calculate Annualized Expected Returns (Assuming 252 trading days)
        annualized_returns = daily_returns.mean() * 252
        
        # 5. Calculate Annualized Covariance Matrix
        cov_matrix = daily_returns.cov() * 252
        
        # Ensure all requested symbols exist in the matrices (handle failed ingestions)
        for sym in symbols:
            if sym not in annualized_returns.index:
                annualized_returns[sym] = 0.0
                cov_matrix[sym] = 0.0
                cov_matrix.loc[sym] = 0.0
                cov_matrix.loc[sym, sym] = 0.04 # Safe dummy variance

        return annualized_returns[symbols], cov_matrix.loc[symbols, symbols]
