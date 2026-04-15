import requests
import time

stock_id = "2330"

def get_stock_price():
    url = f"https://api.allorigins.win/raw?url=https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"

    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200 or not res.text:
            print("API 沒回資料")
            return

        data = res.json()

        if data.get("msgArray"):
            price = data["msgArray"][0].get("z", "無成交")
            print(f"目前價格: {price}")
        else:
            print("抓不到資料")

    except Exception as e:
        print("錯誤:", e)


while True:
    get_stock_price()
    time.sleep(60)
