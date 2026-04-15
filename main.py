import requests
import time

# ====== 你的設定 ======
TOKEN = "ZMvaknwB2/EU4PPjVhls/DCb8dITxVZjDLtbArfPVskXt6unAXNSpQOc1Rv7V/C7rc5QHaOW7lzKSPsBH4t730 tFj6492Gea9+caOScXpU1eHUHrJOa4tcbWdhlJ8l06PEpY1Y71xcI0oYZBeRqk5QdB04t89/1O/w1cDnyilFU=".strip()
USER_ID = "Ue4ac469ed010e1cebba684c8cb399ae5".strip()

# ====== LINE推播 ======
def send_line(msg):
    try:
        url = "https://api.line.me/v2/bot/message/push"

        headers = {
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json"
        }

        data = {
            "to": USER_ID,
            "messages": [{"type": "text", "text": msg}]
        }

        r = requests.post(url, headers=headers, json=data, timeout=10)
        print("LINE:", r.status_code)

    except Exception as e:
        print("LINE錯誤:", e)


# ====== RSI ======
def calculate_rsi(data, period=14):
    gains, losses = [], []

    for i in range(1, len(data)):
        diff = data[i]["close"] - data[i-1]["close"]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ====== 大盤判斷 ======
def market_ok():
    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=TAIEX"
        res = requests.get(url, timeout=10).json()
        data = res.get("data", [])

        if len(data) < 20:
            return False

        close = data[-1]["close"]
        ma20 = sum(d["close"] for d in data[-20:]) / 20

        return close > ma20
    except:
        return False


# ====== 股票清單 ======
def get_all_stocks():
    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
        res = requests.get(url, timeout=10).json()
        data = res.get("data", [])
        return [d["stock_id"] for d in data][:200]  # 控制數量避免爆掉
    except:
        return []


# ====== 股價 ======
def get_price(stock_id):
    try:
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={stock_id}"
        return requests.get(url, timeout=10).json().get("data", [])
    except:
        return []


# ====== 三大法人 ======
def get_inst(stock_id):
    try:
        url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={stock_id}"
        return requests.get(url, timeout=10).json().get("data", [])
    except:
        return []


# ====== 選股邏輯 ======
def is_hot(price, inst):
    if len(price) < 30 or len(inst) < 10:
        return False

    t = price[-1]

    close = t["close"]
    high = t["max"]
    low = t["min"]
    open_p = t["open"]
    vol = t["Trading_Volume"]

    # 🔥 基本條件
    if vol < 2000:
        return False

    vol5 = sum(d["Trading_Volume"] for d in price[-5:]) / 5
    ma5 = sum(d["close"] for d in price[-5:]) / 5
    ma10 = sum(d["close"] for d in price[-10:]) / 10
    ma20 = sum(d["close"] for d in price[-20:]) / 20
    high20 = max(d["close"] for d in price[-20:])

    rsi = calculate_rsi(price)

    # 🔥 三大法人
    last3 = inst[-3:]

    foreign = sum(d["buy_sell"] for d in last3 if d["name"] == "Foreign_Investor")
    trust = sum(d["buy_sell"] for d in last3 if d["name"] == "Investment_Trust")
    dealer = sum(d["buy_sell"] for d in last3 if d["name"] == "Dealer")

    change = (close - price[-2]["close"]) / price[-2]["close"] * 100
    strong = close >= high * 0.9

    return (
        vol > vol5 * 2 and            # 爆量
        close >= high20 and          # 突破
        ma5 > ma10 > ma20 and        # 多頭
        close > open_p and           # 紅K
        rsi > 60 and                 # 強勢
        change > 3 and               # 漲幅
        strong and                   # 收高
        foreign > 0 and trust > 0 and dealer > 0  # 三大法人買
    )


# ====== 掃描 ======
def scan():
    print("🚀 掃描中...")

    if not market_ok():
        msg = "⚠️ 大盤偏弱，今日觀望"
        print(msg)
        send_line(msg)
        return

    stocks = get_all_stocks()

    found = False

    for s in stocks:
        try:
            price = get_price(s)
            inst = get_inst(s)

            if is_hot(price, inst):
                found = True
                t = price[-1]

                msg = f"""🔥 主力飆股：{s}

📈 買點：突破 {t["max"]}
🛑 停損：{t["min"]}
💰 現價：{t["close"]}

策略：爆量＋法人＋突破
"""
                print(msg)
                send_line(msg)

        except Exception as e:
            print("單檔錯誤:", s, e)

    if not found:
        print("❌ 今日無訊號")


# ====== 主程式 ======
while True:
    scan()
    time.sleep(600)  # 每10分鐘掃一次
