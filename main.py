import requests
import time

# ===== RSI 計算 =====
def calculate_rsi(data, period=14):
    gains = []
    losses = []

    for i in range(1, len(data)):
        change = data[i]["close"] - data[i-1]["close"]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ===== 取得股票清單 =====
def get_all_stocks():
    url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
    res = requests.get(url)
    data = res.json()["data"]

    stocks = [d["stock_id"] for d in data if d["industry_category"]]
    return stocks[:300]  # 可調整


# ===== 取得價格 =====
def get_stock_data(stock_id):
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={stock_id}&start_date=2024-03-01"
    try:
        res = requests.get(url, timeout=10)
        return res.json()["data"]
    except:
        return []


# ===== 主力選股邏輯 =====
def is_hot_stock(data):
    if len(data) < 30:
        return False

    today = data[-1]

    close = today["close"]
    open_price = today["open"]
    volume = today["Trading_Volume"]

    # 過濾冷門股
    if volume < 2000:
        return False

    # 均量
    vol5 = sum(d["Trading_Volume"] for d in data[-5:]) / 5

    # 均線
    ma5 = sum(d["close"] for d in data[-5:]) / 5
    ma10 = sum(d["close"] for d in data[-10:]) / 10
    ma20 = sum(d["close"] for d in data[-20:]) / 20

    # 高點
    high20 = max(d["close"] for d in data[-20:])

    # RSI
    rsi = calculate_rsi(data)

    # ===== 條件 =====
    cond1 = volume > vol5 * 2          # 爆量
    cond2 = close >= high20            # 突破
    cond3 = ma5 > ma10 > ma20          # 多頭
    cond4 = close > open_price         # 紅K
    cond5 = rsi > 60                   # 動能

    return cond1 and cond2 and cond3 and cond4 and cond5


# ===== 掃描 =====
def scan_market():
    print("🚀 主力掃描開始...")

    stocks = get_all_stocks()
    hot = []

    for stock in stocks:
        data = get_stock_data(stock)

        if is_hot_stock(data):
            hot.append(stock)
            print(f"🔥 主力進場：{stock}")

    if not hot:
        print("❌ 今天沒有主力股")
    else:
        print("==== 🎯 主力飆股 ====")
        for s in hot:
            print(s)


# ===== 執行 =====
while True:
    scan_market()
    time.sleep(600)
