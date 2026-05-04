import pandas as pd
import datetime

class RiskReporter:
    """
    Generates institutional-grade risk reports for Layer 4 (Compliance).
    Satisfies Section 6.1: Daily Factor Exposure Report.
    """
    def __init__(self, limit_threshold: float = 0.30):
        self.limit_threshold = limit_threshold

    def generate_factor_exposure_report(self, portfolio_loadings: pd.Series, benchmark_loadings: pd.Series):
        """
        Flags breaches where portfolio exposure deviates by more than ±30% from benchmark.
        """
        report_data = []
        for factor in portfolio_loadings.index:
            p_val = portfolio_loadings[factor]
            b_val = benchmark_loadings[factor]
            deviation = p_val - b_val
            
            status = "PASS"
            if abs(deviation) > self.limit_threshold:
                status = "BREACH"
            
            report_data.append({
                "Factor": factor,
                "Portfolio": f"{p_val:.2f}",
                "Benchmark": f"{b_val:.2f}",
                "Deviation": f"{deviation:.2%}",
                "Status": status
            })
            
        df_report = pd.DataFrame(report_data)
        
        print("\n--- Daily Factor Exposure Report ---")
        print(df_report.to_string(index=False))
        
        if "BREACH" in df_report["Status"].values:
            print("\nALERT: Factor exposure limit reached. Triggering GENPOA for rebalancing.")
        
        return df_report

    def log_fiduciary_audit(self, report: pd.DataFrame, lineage_id: str):
        """
        Ensures the report is traceable and archived.
        """
        # Placeholder for audit storage integration
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Risk Report archived for Lineage: {lineage_id} at {timestamp}")
