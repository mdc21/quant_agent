from core.data.mfapi_client import MFApiClient

client = MFApiClient()
codes = ["120586", "103504", "147701", "120594"] 

for code in codes:
    name, df = client.get_historical_navs(code)
    if df.empty:
        print(f"Failed to fetch NAVs for {code}")
    else:
        print(f"Success! {name} has {len(df)} rows.")
