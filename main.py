import requests
import time

# ===== RSI =====
def calculate_rsi(data, period=14):
    gains, losses = [], []

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


# ===== 大盤濾網 =====
def market_ok():
    url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=TAIEX&start_date=2024-03-01"
    try:
        data = requests.get(url).json()["data"]
        if len(data) < 20:
            return False

        close = data[-1]["close"]
        ma20 = sum(d["close"] for d in data[-20:]) / 20

        return close > ma20
    except:
        return False


# ===== 股票清單 =====
def get_all_stocks():
    url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
    res = requests.get(url)
    data = res.json()["data"]

    stocks = [d["stock_id"] for d in data if d["industry_category"]]
    return stocks[:300]   # ⚠️ 可調整（免費API限制）


# ===== 價格資料 =====
def get_price(stock_id):
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={stock_id}&start_date=2024-03-01"
    try:
        return requests.get(url, timeout=10).json()["data"]
    except:
        return []


# ===== 法人資料 =====
def get_institution(stock_id):
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={stock_id}&start_date=2024-03-01"
    try:
        return requests.get(url, timeout=10).json()["data"]
    except:
        return []


# ===== 高勝率主力判斷 =====
def is_hot(price, inst):
    if len(price) < 30 or len(inst) < 10:
        return False

    today = price[-1]

    close = today["close"]
    open_price = today["open"]
    high = today["max"]
    volume = today["Trading_Volume"]

    # 過濾垃圾股
    if volume < 2000:
        return False

    # ===== 技術面 =====
    vol5 = sum(d["Trading_Volume"] for d in price[-5:]) / 5
    ma5 = sum(d["close"] for d in price[-5:]) / 5
    ma10 = sum(d["close"] for d in price[-10:]) / 10
    ma20 = sum(d["close"] for d in price[-20:]) / 20
    high20 = max(d["close"] for d in price[-20:])

    rsi = calculate_rsi(price)

    # ===== 三大法人 =====
    last3 = inst[-3:]

    foreign = sum(d["buy_sell"] for d in last3 if d["name"] == "Foreign_Investor")
    trust = sum(d["buy_sell"] for d in last3 if d["name"] == "Investment_Trust")
    dealer = sum(d["buy_sell"] for d in last3 if d["name"] == "Dealer")

    cond_inst = foreign > 0 and trust > 0 and dealer > 0

    # ===== 強度 =====
    change_pct = (close - price[-2]["close"]) / price[-2]["close"] * 100
    strong_close = close >= high * 0.9

    # ===== 條件 =====
    cond1 = volume > vol5 * 2
    cond2 = close >= high20
    cond3 = ma5 > ma10 > ma20
    cond4 = close > open_price
    cond5 = rsi > 60
    cond6 = change_pct > 3
    cond7 = strong_close

    return cond1 and cond2 and cond3 and cond4 and cond5 and cond6 and cond7 and cond_inst


# ===== 掃描 =====
def scan():
    print("🚀 高勝率掃描中...")

    if not market_ok():
        print("⚠️ 大盤偏弱，今天不建議進場")
        return

    stocks = get_all_stocks()
    result = []

    for s in stocks:
        price = get_price(s)
        inst = get_institution(s)

        if is_hot(price, inst):
            result.append(s)
            print(f"🔥 主力法人股：{s}")

    if not result:
        print("❌ 今日無符合條件股票")
    else:
        print("==== 🎯 今日強勢股 ====")
        for r in result:
            print(r)


# ===== 主程式 =====
while True:
    scan()
    time.sleep(600)
