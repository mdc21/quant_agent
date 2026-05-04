import yfinance as yf
import requests

# Test 1: yfinance
print("--- YFinance ---")
try:
    ticker = yf.Ticker("NIFTYBEES.NS")
    info = ticker.info
    print("Keys found in yfinance:", list(info.keys())[:10])
    print("Expense Ratio:", info.get("annualReportExpenseRatio"))
except Exception as e:
    print(f"yfinance error: {e}")

# Test 2: Groww Search API
print("\n--- Groww Search API ---")
try:
    url = "https://groww.in/v1/api/search/v1/derived/scheme?available_for_investment=true&doc_type=scheme&q=ICICI%20Prudential%20Midcap%20Fund&size=1"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        print("Groww Search Response:", data.keys())
        if 'content' in data and len(data['content']) > 0:
            fund = data['content'][0]
            print(f"Found: {fund.get('scheme_name')}")
            print(f"Search ID: {fund.get('search_id')}")
    else:
        print(f"Groww error: {res.status_code} {res.text}")
except Exception as e:
    print(f"Groww error: {e}")
