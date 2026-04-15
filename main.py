import requests
import time

stock_id = "2330"

def get_from_yahoo():
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={stock_id}.TW"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        result = data.get("quoteResponse", {}).get("result", [])
        if result:
            return result[0].get("regularMarketPrice")
    except:
        return None

def get_from_twse():
    url = f"http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get("msgArray"):
            return data["msgArray"][0].get("z")
    except:
        return None

def get_stock_price():
    price = get_from_yahoo()

    if price:
        print(f"[Yahoo] 目前價格: {price}")
        return

    print("Yahoo 失敗，改用台股 API...")

    price = get_from_twse()

    if price:
        print(f"[TWSE] 目前價格: {price}")
    else:
        print("全部 API 都失敗")


while True:
    get_stock_price()
    time.sleep(60)
