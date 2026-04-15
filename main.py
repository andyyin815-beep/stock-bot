import requests
import time

stock_id = "2330"

def get_stock_price():
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={stock_id}.TW"

    try:
        res = requests.get(url, timeout=10)

        # 👇 防呆：先確認有回傳內容
        if res.status_code != 200 or not res.text:
            print("API 沒回資料")
            return

        data = res.json()

        result = data.get("quoteResponse", {}).get("result", [])
        if not result:
            print("抓不到股票資料")
            return

        price = result[0].get("regularMarketPrice", "無資料")
        print(f"目前價格: {price}")

    except Exception as e:
        print("錯誤:", e)


while True:
    get_stock_price()
    time.sleep(60)
