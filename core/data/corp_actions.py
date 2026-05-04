import pandas as pd

class CorporateActionEngine:
    """
    Handles automatic adjustments for dividends, splits, and bonus issues.
    Ensures continuity in price series for research agents.
    """
    @staticmethod
    def apply_split(df: pd.DataFrame, ratio: float) -> pd.DataFrame:
        """
        Adjusts price and volume for a stock split.
        Example: 1:10 split (ratio = 10)
        """
        adj_df = df.copy()
        price_cols = ['open', 'high', 'low', 'close']
        
        for col in price_cols:
            if col in adj_df.columns:
                adj_df[col] = adj_df[col] / ratio
        
        if 'volume' in adj_df.columns:
            adj_df['volume'] = adj_df['volume'] * ratio
            
        return adj_df

    @staticmethod
    def compute_total_return(df: pd.DataFrame, dividend: float) -> pd.Series:
        """
        Computes the total return index factor for a dividend.
        """
        # This is a simplified version. Institutional systems usually maintain 
        # an 'Adjustment Factor' column.
        last_price = df['close'].iloc[-1]
        adjustment_factor = (last_price - dividend) / last_price
        return adjustment_factor
