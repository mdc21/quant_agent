from core.data.store import DataStore
store = DataStore()
symbols = store.list_symbols()
print(f"Total entries: {len(symbols)}")
fundamentals = [s for s in symbols if s.startswith("FUNDAMENTALS_")]
prices = [s for s in symbols if not s.startswith("FUNDAMENTALS_") and not s.startswith("AUDIT_")]
print(f"Fundamental records: {len(fundamentals)}")
print(f"Price records: {len(prices)}")

# Check for a few from the user's recent log
for check in ["CROMPTON", "LT", "M&MFIN", "IGL"]:
    has_p = check in prices
    has_f = f"FUNDAMENTALS_{check}" in fundamentals
    print(f"{check} -> Price: {has_p}, Fundamental: {has_f}")
