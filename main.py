import requests
import time

stock_id = "2330"

def get_stock_price():
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={stock_id}&start_date=2024-04-01"

    try:
        res = requests.get(url, timeout=10)
        data = res.json()

        if data["data"]:
            price = data["data"][-1]["close"]
            print(f"目前價格: {price}")
        else:
            print("抓不到資料")

    except Exception as e:
        print("錯誤:", e)


while True:
    get_stock_price()
    time.sleep(60)
