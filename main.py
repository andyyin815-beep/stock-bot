import requests
import time

# 台股清單（先抓幾檔示範，之後可擴充）
stocks = ["2330", "2317", "2454", "2303", "1301"]

def get_stock_data(stock_id):
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={stock_id}&start_date=2024-03-01"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()["data"]
        return data
    except:
        return []

def is_hot_stock(data):
    if len(data) < 20:
        return False

    # 最新資料
    today = data[-1]
    close = today["close"]
    volume = today["Trading_Volume"]

    # 5日平均量
    vol_5 = sum([d["Trading_Volume"] for d in data[-5:]]) / 5

    # 20日最高
    high_20 = max([d["close"] for d in data[-20:]])

    # 簡單條件
    cond1 = volume > vol_5 * 2
    cond2 = close >= high_20
    cond3 = close > data[-2]["close"]

    return cond1 and cond2 and cond3

def scan_market():
    hot_stocks = []

    for stock in stocks:
        data = get_stock_data(stock)
        if is_hot_stock(data):
            hot_stocks.append(stock)

    if hot_stocks:
        print("🔥 今日可能飆股：")
        for s in hot_stocks:
            print(s)
    else:
        print("今天沒有符合條件的飆股")

# 每5分鐘掃一次
while True:
    scan_market()
    time.sleep(300)
