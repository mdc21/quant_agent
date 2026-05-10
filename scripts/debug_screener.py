import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
url = "https://www.screener.in/company/HDFCBANK/consolidated/"
print(f"Fetching {url}...")
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

# Find all ratios in the top section
ratios = []
top_ratios = soup.find('div', class_='company-ratios')
if top_ratios:
    for li in top_ratios.find_all('li'):
        name = li.find('span', class_='name')
        val = li.find('span', class_='number')
        if name and val:
            ratios.append(f"{name.get_text(strip=True)}: {val.get_text(strip=True)}")

print("\n--- TOP RATIOS FOUND ---")
for r in ratios:
    print(r)

# Also check for tables that might contain NIM/GNPA
print("\n--- CHECKING TABLES ---")
for table in soup.find_all('table'):
    header = table.find('th')
    if header:
        print(f"Table found with header: {header.get_text(strip=True)}")
