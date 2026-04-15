import requests
import time

stock_id = "2330"

def get_stock_price():
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={stock_id}.TW"

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        price = data["quoteResponse"]["result"][0]["regularMarketPrice"]
        print(f"目前價格: {price}")

    except Exception as e:
        print("錯誤:", e)


while True:
    get_stock_price()
    time.sleep(60)
