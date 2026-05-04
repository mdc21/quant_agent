import yfinance as yf
import pandas as pd
import numpy as np
from core.utils.logger import get_data_logger

logger = get_data_logger("YFinanceClient")

class YFinanceClient:
    """
    Primary API Feed: Yahoo Finance.
    Used to pull fundamental data (Income, Balance Sheet, Cash Flow).
    """
    def __init__(self):
        pass

    def get_latest_fundamentals(self, symbol: str) -> dict:
        logger.info(f"Fetching fundamentals for {symbol}...")
        yf_symbol = f"{symbol}.NS" if not symbol.endswith(('.NS', '.BO')) else symbol
        
        try:
            ticker = yf.Ticker(yf_symbol)
            
            # Force Annual data to match Screener's Annual tables
            inc = ticker.income_stmt
            bs = ticker.balance_sheet
            cf = ticker.cashflow
            
            if inc.empty or bs.empty or cf.empty:
                logger.error(f"Missing annual data for {yf_symbol}.")
                return {}
                
            # yfinance returns DataFrames where columns are dates, latest is typically col 0
            latest_date = inc.columns[0]
            
            def safe_get(df: pd.DataFrame, key: str) -> float:
                if key in df.index:
                    # Handle if the row is returned as a Series or multiple rows
                    val = df.loc[key].iloc[0] if isinstance(df.loc[key], pd.Series) else df.loc[key]
                    try:
                        return float(val) if not pd.isna(val) else 0.0
                    except:
                        return 0.0
                return 0.0

            # Map the standard YF indices
            net_income = safe_get(inc, "Net Income")
            revenue = safe_get(inc, "Total Revenue")
            total_assets = safe_get(bs, "Total Assets")
            
            # Liabilities usually require a specific key in YF
            total_liabilities = safe_get(bs, "Total Liabilities Net Minority Interest")
            if total_liabilities == 0.0:
                total_liabilities = safe_get(bs, "Total Debt")
                
            operating_cash_flow = safe_get(cf, "Operating Cash Flow")

            logger.info(f"Successfully extracted fundamentals for {yf_symbol}")

            # --- Multi-year FCF and ROCE (P3 extension) ---
            # FCF = Operating Cash Flow - Capital Expenditures (per year)
            fcf_positive_years = 0
            fcf_years_checked = 0
            try:
                if not cf.empty:
                    # yfinance columns are dates (latest first)
                    years_available = min(4, len(cf.columns))
                    for col in cf.columns[:years_available]:
                        ocf = float(cf.loc["Operating Cash Flow", col]) if "Operating Cash Flow" in cf.index else 0.0
                        capex = 0.0
                        for capex_key in ["Capital Expenditure", "Capital Expenditures"]:
                            if capex_key in cf.index:
                                capex = abs(float(cf.loc[capex_key, col]))
                                break
                        fcf = ocf - capex
                        if fcf > 0:
                            fcf_positive_years += 1
                        fcf_years_checked += 1
            except Exception as e:
                logger.warning(f"FCF multi-year failed for {symbol}: {e}")

            # ROCE = EBIT / Capital Employed
            # EBIT ≈ Operating Income (from income stmt)
            # Capital Employed = Total Assets - Current Liabilities
            roce = 0.0
            try:
                ebit = 0.0
                for ebit_key in ["Operating Income", "EBIT"]:
                    if ebit_key in inc.index:
                        ebit = safe_get(inc, ebit_key)
                        break
                current_liab = safe_get(bs, "Current Liabilities") or safe_get(bs, "Total Current Liabilities")
                capital_employed = total_assets - current_liab
                if capital_employed > 0:
                    roce = ebit / capital_employed
            except Exception as e:
                logger.warning(f"ROCE computation failed for {symbol}: {e}")

            return {
                "symbol": symbol,
                "date": str(latest_date),
                "net_income": net_income,
                "total_revenue": revenue,
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "operating_cash_flow": operating_cash_flow,
                "roce": roce,
                "fcf_positive_years": fcf_positive_years,
                "fcf_years_checked": fcf_years_checked,
                "source": "YFINANCE"
            }
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")
            return {}
