import requests
import json
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("1. Testing AMFI Text Screener...")
    try:
        res = requests.get("https://www.amfiindia.com/spages/NAVAll.txt", timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            lines = res.text.split('\n')
            print(f"Total lines downloaded: {len(lines)}")
            candidates = []
            for line in lines:
                if "Direct" in line and "Growth" in line and "IDCW" not in line and "Dividend" not in line:
                    parts = line.split(';')
                    if len(parts) >= 6:
                        name = parts[3].lower()
                        if any(x in name for x in ["index", "midcap", "smallcap", "technology", "nifty"]):
                            candidates.append(parts[0])
            print(f"Found {len(candidates)} matching funds.")
            if candidates:
                print(f"Sample: {candidates[:5]}")
    except Exception as e:
        print(f"Failed: {e}")

    print("\n2. Testing MFAPI.in...")
    try:
        # 120586 is ICICI Pru Midcap
        url = "https://api.mfapi.in/mf/120586"
        res = requests.get(url, timeout=10)
        print(f"Status: {res.status_code}")
        data = res.json()
        print(f"Status in JSON: {data.get('status')}")
        if data.get('data'):
            print(f"History length: {len(data['data'])}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()
