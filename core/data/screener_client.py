import requests
import pandas as pd
from bs4 import BeautifulSoup
from core.utils.logger import get_data_logger

logger = get_data_logger("ScreenerClient")

class ScreenerClient:
    """
    Verification Feed: Screener.in
    Scrapes standard fundamental tables to cross-check Primary APIs.
    """
    def __init__(self):
        self.base_url = "https://www.screener.in/company"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _clean_number(self, val) -> float:
        if pd.isna(val):
            return 0.0
        val_str = str(val).replace(',', '').strip()
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    def _extract_metric(self, df: pd.DataFrame, latest_col: str, keyword: str) -> float:
        """Finds a row matching the keyword (case-insensitive, ignoring extra chars) and returns its cleaned value."""
        for idx in df.index:
            if isinstance(idx, str) and keyword.lower() in idx.lower():
                val = df.loc[idx, latest_col]
                return self._clean_number(val.iloc[0] if isinstance(val, pd.Series) else val) * 10_000_000
        return None

    def get_latest_fundamentals(self, symbol: str) -> dict:
        """
        Scrapes P&L, Balance Sheet, and Cash Flows from Screener.
        Returns values multiplied by 1 Crore (10,000,000) to match YFinance's raw precision.
        """
        # Clean symbol
        clean_sym = symbol.replace(".NS", "").replace(".BO", "")
        
        logger.info(f"Scraping Screener.in for {clean_sym}...")
        url = f"{self.base_url}/{clean_sym}/consolidated/"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                # Fallback to standalone if consolidated doesn't exist
                url = f"{self.base_url}/{clean_sym}/"
                response = requests.get(url, headers=self.headers, timeout=10)
                
            if response.status_code != 200:
                logger.error(f"Failed to fetch Screener page for {clean_sym} (HTTP {response.status_code})")
                return {}
                
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            fundamentals = {
                "symbol": clean_sym,
                "source": "SCREENER_IN"
            }
            
            # 1. Profit & Loss
            pl_section = soup.find(id="profit-loss")
            if pl_section:
                import io
                df_pl = pd.read_html(io.StringIO(str(pl_section)))[0]
                df_pl = df_pl.set_index(df_pl.columns[0])
                
                # Exclude TTM column if it exists to compare Annual against Annual
                cols = [c for c in df_pl.columns if "TTM" not in str(c)]
                if cols:
                    latest_col = cols[-1]
                    fundamentals["date"] = str(latest_col)
                    
                    val_net = self._extract_metric(df_pl, latest_col, "net profit")
                    if val_net is not None: fundamentals["net_income"] = val_net
                        
                    val_rev = self._extract_metric(df_pl, latest_col, "sales")
                    if val_rev is not None: fundamentals["total_revenue"] = val_rev
                    # Some companies use 'Revenue' instead of 'Sales'
                    if fundamentals.get("total_revenue") is None:
                        val_rev2 = self._extract_metric(df_pl, latest_col, "revenue")
                        if val_rev2 is not None: fundamentals["total_revenue"] = val_rev2
                else:
                    logger.warning(f"No valid annual columns found for {clean_sym} in P&L.")

            # 2. Balance Sheet
            bs_section = soup.find(id="balance-sheet")
            if bs_section:
                import io
                df_bs = pd.read_html(io.StringIO(str(bs_section)))[0]
                df_bs = df_bs.set_index(df_bs.columns[0])
                latest_col = df_bs.columns[-1]
                
                val_assets = self._extract_metric(df_bs, latest_col, "total assets")
                if val_assets is not None: fundamentals["total_assets"] = val_assets
                    
                val_liab = self._extract_metric(df_bs, latest_col, "total liabilities")
                if val_liab is not None: 
                    fundamentals["total_liabilities"] = val_liab
                elif "total_assets" in fundamentals:
                    # Balance Sheet equation fallback
                    fundamentals["total_liabilities"] = fundamentals["total_assets"]

            # 3. Cash Flow
            cf_section = soup.find(id="cash-flow")
            if cf_section:
                import io
                df_cf = pd.read_html(io.StringIO(str(cf_section)))[0]
                df_cf = df_cf.set_index(df_cf.columns[0])
                latest_col = df_cf.columns[-1]
                
                val_cf = self._extract_metric(df_cf, latest_col, "operating activity")
                if val_cf is not None: fundamentals["operating_cash_flow"] = val_cf

            logger.info(f"Successfully scraped Screener.in fundamentals for {clean_sym}")
            return fundamentals
            
        except Exception as e:
            logger.error(f"Screener.in scraping failed for {clean_sym}: {e}")
            return {}

    def get_roce_and_fcf(self, symbol: str) -> dict:
        """
        Scrapes ROCE (%) from Screener's key ratios section and multi-year FCF
        from the cash flow table. Returns a supplemental dict to enrich fundamentals.
        """
        clean_sym = symbol.replace(".NS", "").replace(".BO", "")
        url = f"{self.base_url}/{clean_sym}/consolidated/"

        result = {"roce": None, "fcf_positive_years": None, "fcf_years_checked": None}
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                url = f"{self.base_url}/{clean_sym}/"
                response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # 1. ROCE from key ratios table
            ratios_section = soup.find(id="top-ratios")
            if ratios_section:
                for li in ratios_section.find_all("li"):
                    name_span = li.find("span", class_="name")
                    val_span = li.find("span", class_="nowrap")
                    if name_span and val_span:
                        if "ROCE" in name_span.get_text(strip=True):
                            try:
                                result["roce"] = float(val_span.get_text(strip=True).replace("%", "").replace(",", "")) / 100
                            except ValueError:
                                pass
                            break

            # 2. Multi-year FCF from cash flow table
            cf_section = soup.find(id="cash-flow")
            if cf_section:
                import io
                df_cf = pd.read_html(io.StringIO(str(cf_section)))[0]
                df_cf = df_cf.set_index(df_cf.columns[0])

                # Screener labels: "Cash from Operations", "Cash from Investing" (Capex is negative)
                fcf_positive = 0
                fcf_checked = 0
                # Exclude TTM column
                cols = [c for c in df_cf.columns if "TTM" not in str(c)]
                if not cols:
                    return result
                    
                years = cols[-4:] if len(cols) >= 4 else cols  # Up to 4 years

                for year_col in years:
                    ocf = None
                    capex = None
                    for idx in df_cf.index:
                        if isinstance(idx, str):
                            if "operating" in idx.lower():
                                ocf = self._clean_number(df_cf.loc[idx, year_col]) * 10_000_000
                            if "investing" in idx.lower():
                                # Capex is the dominant use of investing cash; treat negative as capex
                                raw = self._clean_number(df_cf.loc[idx, year_col]) * 10_000_000
                                capex = abs(raw) if raw < 0 else 0
                    if ocf is not None and capex is not None:
                        fcf = ocf - capex
                        if fcf > 0:
                            fcf_positive += 1
                        fcf_checked += 1

                if fcf_checked > 0:
                    result["fcf_positive_years"] = fcf_positive
                    result["fcf_years_checked"] = fcf_checked

            logger.info(f"Screener ROCE/FCF for {clean_sym}: {result}")
            return result

        except Exception as e:
            logger.error(f"Screener ROCE/FCF scrape failed for {clean_sym}: {e}")
            return result

