import os
import xml.etree.ElementTree as ET

class XBRLVerifier:
    """
    Verification Feed: XBRL (Extensible Business Reporting Language)
    Acts as the Cryptographic-style "Source of Truth" for fundamental data.
    Reads regulatory filings downloaded from NSE/BSE.
    """
    def __init__(self, xbrl_dir: str = "app/data/xbrl/"):
        self.xbrl_dir = xbrl_dir
        os.makedirs(self.xbrl_dir, exist_ok=True)

    def _strip_namespace(self, tag: str) -> str:
        """Removes the {namespace} from XML tags for easier matching."""
        if '}' in tag:
            return tag.split('}', 1)[1]
        return tag

    def parse_xbrl(self, filepath: str) -> dict:
        """
        Parses an XBRL XML file to extract key financial metrics.
        Returns a standardized dictionary.
        """
        if not os.path.exists(filepath):
            print(f"XBRL File not found: {filepath}")
            return {}

        extracted_data = {
            "net_income": None,
            "total_revenue": None,
            "total_assets": None,
            "total_liabilities": None,
            "operating_cash_flow": None
        }

        # Indian Accounting Standards (Ind-AS) typical tags
        tag_mappings = {
            "net_income": ["ProfitLoss", "ProfitForPeriod", "ProfitLossForPeriod"],
            "total_revenue": ["RevenueFromOperations", "TotalRevenue"],
            "total_assets": ["TotalAssets", "Assets"],
            "total_liabilities": ["TotalLiabilities", "Liabilities"],
            "operating_cash_flow": ["NetCashFlowsFromUsedInOperatingActivities", "CashFlowsFromUsedInOperatingActivities"]
        }

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            for elem in root.iter():
                clean_tag = self._strip_namespace(elem.tag)
                
                # In a full XBRL parser, we would filter by the 'contextRef' attribute for the exact quarter.
                if elem.text and elem.text.strip().lstrip('-').replace('.', '', 1).isdigit():
                    value = float(elem.text.strip())
                    
                    for metric, possible_tags in tag_mappings.items():
                        if extracted_data[metric] is None and any(t.lower() in clean_tag.lower() for t in possible_tags):
                            extracted_data[metric] = value
                            break

            extracted_data["source"] = "XBRL_SOURCE_OF_TRUTH"
            return extracted_data
            
        except Exception as e:
            print(f"Failed to parse XBRL file {filepath}: {e}")
            return {}

    def get_latest_fundamentals(self, symbol: str) -> dict:
        """
        Locates the latest XBRL filing for the symbol and parses it.
        """
        expected_file = os.path.join(self.xbrl_dir, f"{symbol}_latest.xml")
        
        data = self.parse_xbrl(expected_file)
        if data:
            data["symbol"] = symbol
        return data
