import requests
import time

# 取得台股清單（上市）
def get_all_stocks():
    url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
    res = requests.get(url)
    data = res.json()["data"]

    # 只留上市股票
    stocks = [d["stock_id"] for d in data if d["industry_category"]]
    return stocks[:200]  # ⚠️ 先限制200檔避免爆API（可之後放大）


def get_stock_data(stock_id):
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={stock_id}&start_date=2024-03-01"
    try:
        res = requests.get(url, timeout=10)
        return res.json()["data"]
    except:
        return []


def is_hot_stock(data):
    if len(data) < 20:
        return False

    # 最新
    today = data[-1]
    close = today["close"]
    volume = today["Trading_Volume"]

    # 過濾太小成交量（避免垃圾股）
    if volume < 1000:
        return False

    # 5日均量
    vol5 = sum(d["Trading_Volume"] for d in data[-5:]) / 5

    # 均線
    ma5 = sum(d["close"] for d in data[-5:]) / 5
    ma10 = sum(d["close"] for d in data[-10:]) / 10
    ma20 = sum(d["close"] for d in data[-20:]) / 20

    # 20日最高
    high20 = max(d["close"] for d in data[-20:])

    # 條件
    cond1 = volume > vol5 * 2            # 爆量
    cond2 = close >= high20              # 突破
    cond3 = ma5 > ma10 > ma20            # 多頭排列
    cond4 = close > data[-2]["close"]    # 當日上漲

    return cond1 and cond2 and cond3 and cond4


def scan_market():
    print("開始掃描市場...")

    stocks = get_all_stocks()
    hot = []

    for stock in stocks:
        data = get_stock_data(stock)
        if is_hot_stock(data):
            hot.append(stock)
            print(f"🔥 發現飆股：{stock}")

    if not hot:
        print("今天沒有符合條件的股票")
    else:
        print("==== 今日飆股清單 ====")
        for s in hot:
            print(s)


# 每10分鐘掃一次（避免API爆）
while True:
    scan_market()
    time.sleep(600)
