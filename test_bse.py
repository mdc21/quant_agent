import requests

url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json"
}
params = {
    "pageno": 1,
    "strCat": "-1",
    "strPrevDate": "20240101",
    "strScrip": "500325",
    "strSearch": "P",
    "strToDate": "20240427",
    "strType": "C"
}
response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.text[:500])
