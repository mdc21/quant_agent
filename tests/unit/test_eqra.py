import sys
from app.agents.eqra import EquityResearchAgent

eqra = EquityResearchAgent()
candidates = eqra.screen_stocks("NIFTY 50")

print(f"\nTotal candidates that passed the screen: {len(candidates)}")
for c in candidates:
    print(f"- {c.symbol}: {c.rationale}")

# Let's also print why some might have failed by overriding the screen
print("\n--- Why others failed ---")
from core.data.store import DataStore
store = DataStore()
lib = store.lib
from core.data.universe_fetcher import UniverseFetcher
symbols = UniverseFetcher().get_universe("NIFTY 50")

failed = 0
for sym in symbols:
    symbol_key = f"FUNDAMENTALS_{sym}"
    if lib.has_symbol(symbol_key):
        df = lib.read(symbol_key).data
        if not df.empty:
            fund = df.iloc[0].to_dict()
            assets = fund.get('total_assets', 0)
            net_income = fund.get('net_income', 0)
            roa = (net_income / assets) if assets > 0 else 0
            q_score = eqra.calculate_qarp_score(fund)
            
            passes = (q_score >= 2 and roa >= 0.05)
            if not passes:
                failed += 1
                if failed <= 5:
                    print(f"{sym} Failed -> Q_Score: {q_score}, ROA: {roa:.2%}")

print(f"\nTotal failed: {failed}")
