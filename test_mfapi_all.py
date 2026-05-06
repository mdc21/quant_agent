import requests

def main():
    try:
        res = requests.get("https://api.mfapi.in/mf", timeout=15)
        print(f"Status: {res.status_code}")
        data = res.json()
        print(f"Total funds returned: {len(data)}")
        if len(data) > 0:
            print("Sample:")
            for i in range(5):
                print(data[i])
            
            # Count how many match our criteria
            count = 0
            for f in data:
                name = str(f.get("schemeName", "")).lower()
                if "direct" in name and "growth" in name and "idcw" not in name and "dividend" not in name:
                    if any(x in name for x in ["index", "midcap", "smallcap", "technology", "nifty"]):
                        count += 1
            print(f"Found {count} matching funds from mfapi.in!")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
