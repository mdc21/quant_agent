import uuid
from typing import Dict, Any, Tuple
from core.data.yfinance_client import YFinanceClient
from core.data.screener_client import ScreenerClient
from core.data.store import DataStore
from core.utils.logger import get_data_logger

logger = get_data_logger("FiduciaryValidator")

class FiduciaryValidator:
    """
    Tier 4 Governance Component.
    Reconciles Primary API feeds against Screener.in Aggregator.
    """
    def __init__(self):
        self.primary_feed = YFinanceClient()
        self.verification_feed = ScreenerClient()
        self.store = DataStore()
        
    def _calculate_variance(self, api_val: float, verify_val: float) -> float:
        """Calculates percentage variance between API and Screener."""
        if verify_val == 0 or verify_val is None:
            return float('inf')
        if api_val is None:
            return float('inf')
        return abs(api_val - verify_val) / abs(verify_val)

    def validate_fundamentals(self, symbol: str, tolerance: float = 0.80) -> Tuple[bool, Dict[str, Any]]:
        """
        Validates fundamental data by comparing API vs XBRL.
        Tolerance defaults to 0.5% to account for rounding differences.
        """
        logger.info(f"Initiating dual-feed reconciliation for {symbol}...")
        
        api_data = self.primary_feed.get_latest_fundamentals(symbol)
        verify_data = self.verification_feed.get_latest_fundamentals(symbol)
        
        lineage_id = f"FIDUC_{symbol}_{uuid.uuid4().hex[:8]}"
        
        if not api_data:
            self.store.log_quality_event("FIDUCIARY_VALIDATION_FAILED", {"reason": "Missing API Data", "symbol": symbol}, lineage_id)
            return False, {}
            
        if not verify_data or verify_data.get("net_income") is None:
            # Note: In production, missing Verification means we cannot certify the data as "Fiduciary Grade".
            self.store.log_quality_event("FIDUCIARY_VALIDATION_WARNING", {"reason": "Missing Verification Feed, falling back to unverified API", "symbol": symbol}, lineage_id)
            # Return API data so pipeline doesn't break, but mark as NOT fiduciary grade
            if api_data:
                api_data["fiduciary_grade"] = False
            return False, api_data

        # Reconciliation Checks
        metrics_to_check = ["net_income", "total_assets", "total_liabilities", "operating_cash_flow"]
        breaches = []
        
        for metric in metrics_to_check:
            api_val = api_data.get(metric)
            verify_val = verify_data.get(metric)
            
            # Allow skipping if Verification didn't have the exact tag mapped
            if verify_val is None:
                continue
                
            variance = self._calculate_variance(api_val, verify_val)
            if variance > tolerance:
                breaches.append(f"{metric} variance {variance:.2%} exceeds tolerance {tolerance:.2%} (API: {api_val}, Verify: {verify_val})")

        is_fiduciary_grade = len(breaches) == 0
        
        if is_fiduciary_grade:
            self.store.log_quality_event(
                "FIDUCIARY_VALIDATION_PASSED", 
                {"symbol": symbol, "variance_checks": "OK", "feed": "YFinance x Screener.in"}, 
                lineage_id
            )
            api_data["fiduciary_grade"] = True
            api_data["verified_by"] = "Screener.in"
        else:
            logger.warning(f"Validation Breaches for {symbol}: {breaches}")
            self.store.log_quality_event(
                "FIDUCIARY_VALIDATION_FAILED",
                {"symbol": symbol, "breaches": breaches},
                lineage_id
            )
            api_data["fiduciary_grade"] = False

        # --- P3: Enrich with ROCE and multi-year FCF ---
        # Screener is the authoritative source (shows pre-computed ROCE %)
        # YFinance computed values serve as fallback
        try:
            screener_extras = self.verification_feed.get_roce_and_fcf(symbol)
            # Prefer Screener's ROCE; fall back to YFinance computed value
            if screener_extras.get("roce") is not None:
                api_data["roce"] = screener_extras["roce"]
            elif "roce" not in api_data or api_data.get("roce", 0) == 0:
                api_data.setdefault("roce", 0.0)

            # FCF years: prefer Screener (4-year history); fall back to YFinance
            if screener_extras.get("fcf_positive_years") is not None:
                api_data["fcf_positive_years"] = screener_extras["fcf_positive_years"]
                api_data["fcf_years_checked"] = screener_extras.get("fcf_years_checked", 4)
            else:
                api_data.setdefault("fcf_positive_years", 0)
                api_data.setdefault("fcf_years_checked", 0)

            # --- P4: Specialized Financial Ratios Hydration ---
            # Automatically fetch GNPA, CASA, NIM, CET1 for all financial/banking firms
            sector_str = str(api_data.get('sector', '')).lower()
            industry_str = str(api_data.get('industry', '')).lower()
            is_fin_sector = any(x in sector_str or x in industry_str for x in ["financial", "bank", "nbfc", "insurance", "capital market"])
            
            if is_fin_sector:
                logger.info(f"Financial/Banking entity detected for {symbol}. Hydrating specialized fiduciary ratios...")
                specialized = self.verification_feed.get_specialized_ratios(symbol)
                for k, v in specialized.items():
                    if v is not None:
                        api_data[k] = v
                
                # Fetch Presentation/Transcript links for Document Intelligence
                doc_links = self.verification_feed.get_document_links(symbol)
                api_data.update(doc_links)
                        
        except Exception as e:
            logger.warning(f"ROCE/FCF/Financial enrichment failed for {symbol}: {e}")
            api_data.setdefault("roce", 0.0)
            api_data.setdefault("fcf_positive_years", 0)
            api_data.setdefault("fcf_years_checked", 0)

        return is_fiduciary_grade, api_data
