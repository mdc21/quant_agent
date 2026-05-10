import pandas as pd
import numpy as np
from typing import List, Dict, Any
from core.data.agent_schema import StockCandidate

class EquityResearchAgent:
    """
    Equity Research Agent (EQRA).
    The 'Stock Picker' using QARP (Quality at a Reasonable Price).
    Satisfies Task A3 of the Agent Mesh.
    """
    def __init__(self, min_f_score: int = 7, min_roce: float = 0.15):
        self.min_f_score = min_f_score
        self.min_roce = min_roce

    def calculate_qarp_score(self, fundamentals: Dict[str, Any]) -> int:
        """
        Calculates a 4-point Quality At a Reasonable Price (QARP) Score 
        using verified ArcticDB Fiduciary metrics.
        """
        score = 0
        net_income = fundamentals.get('net_income', 0)
        cfo = fundamentals.get('operating_cash_flow', 0)
        assets = fundamentals.get('total_assets', 0)
        liabilities = fundamentals.get('total_liabilities', float('inf'))
        
        # 1. Profitability
        if net_income > 0: score += 1
        
        # 2. Cash Generation
        if cfo > 0: score += 1
        
        # 3. Earnings Quality (Cash > Profit)
        if cfo > net_income: score += 1
        
        # 4. Solvency
        if liabilities < assets: score += 1
            
        return score

    def screen_stocks(self, index_name: str = "NIFTY 50") -> List[StockCandidate]:
        """
        Queries ArcticDB for pre-ingested fundamentals of the target universe.
        """
        from core.data.universe_fetcher import UniverseFetcher
        from core.data.store import DataStore
        
        print(f"EQRA: Initiating screen for universe: {index_name}")
        fetcher = UniverseFetcher()
        store = DataStore()
        lib = store.lib
        
        if index_name == "ALL":
            symbols = [sym.replace("FUNDAMENTALS_", "") for sym in store.list_symbols() if sym.startswith("FUNDAMENTALS_")]
        else:
            symbols = fetcher.get_universe(index_name)
            
        if not symbols:
            print(f"EQRA: No symbols found for {index_name}")
            return []
            
        live_universe = {}
        
        for sym in symbols:
            symbol_key = f"FUNDAMENTALS_{sym}"
            try:
                if lib.has_symbol(symbol_key):
                    df = lib.read(symbol_key).data
                    if not df.empty:
                        fundamentals = df.iloc[0].to_dict()
                        live_universe[sym] = fundamentals
                else:
                    # SELF-HEALING: Fetch missing fundamentals in real-time
                    print(f"EQRA: Missing pre-ingested data for {sym}. Attempting real-time fiduciary hydration...")
                    from core.data.fiduciary_validator import FiduciaryValidator
                    import pandas as pd
                    validator = FiduciaryValidator()
                    is_grade, fundamentals = validator.validate_fundamentals(sym)
                    
                    if fundamentals:
                        fundamentals['fiduciary_grade'] = is_grade
                        # Persist to ArcticDB for future runs
                        df_to_save = pd.DataFrame([fundamentals])
                        if 'date' in df_to_save.columns and not df_to_save['date'].isnull().all():
                            df_to_save['date'] = pd.to_datetime(df_to_save['date'])
                            df_to_save.set_index('date', inplace=True)
                        lib.write(symbol_key, df_to_save)
                        
                        live_universe[sym] = fundamentals
                        print(f"EQRA: Successfully hydrated and persisted fundamentals for {sym}.")
                    else:
                        print(f"EQRA: Real-time hydration failed for {sym}. Stock will be ignored.")
            except Exception as e:
                print(f"EQRA: Error during hydration/reading for {sym}: {e}")

        if not live_universe:
            return []

        # --- P2: Real 12-1 month momentum (replaces flat 0.75 constant) ---
        from core.data.momentum_calculator import MomentumCalculator
        universe_symbols = list(live_universe.keys())
        print(f"EQRA: Computing 12-1 month momentum scores for {len(universe_symbols)} symbols...")
        try:
            calc = MomentumCalculator()
            momentum = calc.compute_momentum_scores(universe_symbols)
        except Exception as e:
            print(f"EQRA: Momentum computation failed ({e}). Falling back to neutral 0.5.")
            momentum = {sym: 0.5 for sym in universe_symbols}
        
        return self.screen_universe(live_universe, momentum)

    def screen_universe(self, universe_fundamentals: Dict[str, Dict[str, Any]], price_momentum: Dict[str, float]) -> List[StockCandidate]:
        """
        Runs the multi-stage sieve to identify candidates using Sector-Specific Fiduciary metrics.
        """
        candidates = []
        
        from core.utils.symbol_mapper import SymbolMapper
        for symbol, fundamentals in universe_fundamentals.items():
            # Re-verify sector via SymbolMapper to ensure rationale labels are correct
            curated_sector = SymbolMapper.get_sector(symbol)
            sector = curated_sector if curated_sector else str(fundamentals.get('sector', 'Unknown'))
            industry = str(fundamentals.get('industry', 'Unknown'))
            
            # --- BASE METRICS ---
            assets = fundamentals.get('total_assets', 0)
            net_income = fundamentals.get('net_income', 0)
            roa = (net_income / assets) if assets > 0 else 0
            q_score = self.calculate_qarp_score(fundamentals)
            
            # --- SECTOR-SPECIFIC SIEVES ---
            passes_fundamental = False
            rationale_parts = []
            
            if "Bank" in industry or "Bank" in sector:
                # BANK SIEVE: Priority = Asset Quality & Funding
                gnpa = fundamentals.get('gnpa')
                casa = fundamentals.get('casa_ratio')
                pcr = fundamentals.get('pcr')
                cet1 = fundamentals.get('cet1')
                
                # Rule: ROA > 1.5% is the primary gate. 
                # If specialized metrics are missing, allow pass but log as 'Unverified'
                passes_bank = (roa >= 0.015)
                
                if gnpa is not None: passes_bank &= (gnpa <= 0.025)
                if cet1 is not None: passes_bank &= (cet1 >= 0.12)
                
                passes_fundamental = passes_bank
                rationale_parts.append(f"BANK: ROA {roa:.1%}")
                if gnpa: rationale_parts.append(f"GNPA {gnpa:.1%}")
                else: rationale_parts.append("GNPA: Unverified")
            
            elif "NBFC" in industry or "Credit Services" in industry:
                # NBFC SIEVE: Priority = Margin & Liquidity
                nim = fundamentals.get('nim')
                gnpa = fundamentals.get('gnpa')
                
                # Rule: ROA > 2.5%
                passes_nbfc = (roa >= 0.025)
                if gnpa is not None: passes_nbfc &= (gnpa <= 0.035)
                
                passes_fundamental = passes_nbfc
                rationale_parts.append(f"NBFC: ROA {roa:.1%}")
                if nim: rationale_parts.append(f"NIM {nim:.1%}")

            elif "Asset Management" in industry or "Capital Markets" in industry:
                # AMC/CAPITAL MARKETS: Priority = Margin & ROCE
                margin = (net_income / fundamentals.get('revenue', 1e9)) if fundamentals.get('revenue', 0) > 0 else 0
                roce = fundamentals.get('roce', 0)
                
                # Rule: ROCE > 25% and Margin > 40%
                passes_capmkt = (
                    roce >= 0.25 and
                    margin >= 0.40
                )
                passes_fundamental = passes_capmkt
                rationale_parts.append(f"CAP_MKT: ROCE {roce:.0%}, Margin {margin:.0%}")
            
            else:
                # STANDARD SECTOR SIEVE: QARP + ROCE
                roce = fundamentals.get('roce', 0)
                fcf_pos = fundamentals.get('fcf_positive_years', 0)
                
                passes_ind = (
                    q_score >= 2 and
                    roa >= 0.015 and
                    (roce >= self.min_roce or roce == 0) and
                    (fcf_pos >= 3 or fcf_pos == 0)
                )
                passes_fundamental = passes_ind
                
                # Use actual sector if available, otherwise 'CORE'
                label = sector.upper() if sector and sector != "Unknown" else "CORE"
                rationale_parts.append(f"{label}: QARP {q_score}/4, ROA {roa:.1%}")

            # --- MOMENTUM OVERLAY ---
            if passes_fundamental:
                momentum_rank = price_momentum.get(symbol, 0.0)
                # Final Conviction Score: 60% Quality + 40% Momentum
                quality_normalized = q_score / 4.0
                conviction = (0.6 * quality_normalized) + (0.4 * momentum_rank)
                
                fiduciary_grade = fundamentals.get('fiduciary_grade', False)
                rationale_parts.append(f"Momentum: {momentum_rank:.0%}ile")
                
                candidates.append(StockCandidate(
                    symbol=symbol,
                    conviction_score=conviction,
                    rationale=" | ".join(rationale_parts),
                    factors={
                        "q_score": q_score,
                        "momentum": momentum_rank,
                        "roa": roa,
                        "sector": sector,
                        "industry": industry,
                        "fiduciary_grade": fiduciary_grade,
                    },
                    lineage_id=fundamentals.get('lineage_id', 'UNKNOWN')
                ))
                
        return sorted(candidates, key=lambda x: x.conviction_score, reverse=True)
