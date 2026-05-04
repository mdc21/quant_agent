import sys
from app.agents.eqra import EquityResearchAgent
from core.data.store import DataStore

eqra = EquityResearchAgent()
store = DataStore()
lib = store.lib

symbols = store.list_symbols()
print(f"Total symbols in DB: {len(symbols)}")

passed = []
failed_roa = 0
failed_q = 0

for sym in symbols:
    if sym.startswith("FUNDAMENTALS_"):
        df = lib.read(sym).data
        if not df.empty:
            fund = df.iloc[0].to_dict()
            assets = fund.get('total_assets', 0)
            net_income = fund.get('net_income', 0)
            roa = (net_income / assets) if assets > 0 else 0
            q_score = eqra.calculate_qarp_score(fund)
            
            if q_score >= 2 and roa >= 0.05:
                passed.append((sym, q_score, roa))
            else:
                if roa < 0.05:
                    failed_roa += 1
                if q_score < 2:
                    failed_q += 1

print(f"\nPassed: {len(passed)}")
for p in passed:
    print(f"{p[0]} - Q: {p[1]}, ROA: {p[2]:.2%}")

print(f"\nFailed ROA (< 5%): {failed_roa}")
print(f"Failed Q Score (< 2): {failed_q}")
