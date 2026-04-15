import requests
import time

TOKEN = "ZMvaknwB2/EU4PPjVhls/DCb8dITxVZjDLtbArfPVskXt6unAXNSpQOc1Rv7V/C7rc5QHaOW7lzKSPsBH4t730 tFj6492Gea9+caOScXpU1eHUHrJOa4tcbWdhlJ8l06PEpY1Y71xcI0oYZBeRqk5QdB04t89/1O/w1cDnyilFU=".strip()
USER_ID = "Ue4ac469ed010e1cebba684c8cb399ae5".strip()

# ====== 防重複通知 ======
notified = set()


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
        requests.post(url, headers=headers, json=data, timeout=10)
    except Exception as e:
        print("LINE錯誤:", e)


# ===== RSI =====
def rsi(data, period=14):
    gains, losses = [], []
    for i in range(1, len(data)):
        diff = data[i]["close"] - data[i-1]["close"]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ===== 大盤過濾 =====
def market_ok():
    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=TAIEX"
        data = requests.get(url).json()["data"]

        close = data[-1]["close"]
        ma20 = sum(d["close"] for d in data[-20:]) / 20

        return close > ma20
    except:
        return False


def get_stocks():
    data = requests.get("https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo").json()["data"]
    return [d["stock_id"] for d in data][:150]


def get_price(s):
    return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={s}").json().get("data", [])


def get_inst(s):
    return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={s}").json().get("data", [])


# ===== 核心策略（升級版） =====
def is_strong(price, inst):

    if len(price) < 30 or len(inst) < 10:
        return False

    t = price[-1]

    close = t["close"]
    high = t["max"]
    low = t["min"]
    open_p = t["open"]
    vol = t["Trading_Volume"]

    # 🚫 避免太小量
    if vol < 3000:
        return False

    # 📊 均線
    ma5 = sum(d["close"] for d in price[-5:]) / 5
    ma10 = sum(d["close"] for d in price[-10:]) / 10
    ma20 = sum(d["close"] for d in price[-20:]) / 20

    # 📈 20日新高
    high20 = max(d["close"] for d in price[-20:])

    # 📊 RSI
    r = rsi(price)

    # 🔥 爆量
    vol5 = sum(d["Trading_Volume"] for d in price[-5:]) / 5

    # 💥 漲幅
    change = (close - price[-2]["close"]) / price[-2]["close"] * 100

    # 🧠 K棒強度（避免長上影）
    body = abs(close - open_p)
    candle = high - low
    strong_k = body / candle > 0.5 if candle != 0 else False

    # 💰 法人（加強版）
    last3 = inst[-3:]

    foreign = sum(d["buy_sell"] for d in last3 if d["name"] == "Foreign_Investor")
    trust = sum(d["buy_sell"] for d in last3 if d["name"] == "Investment_Trust")
    dealer = sum(d["buy_sell"] for d in last3 if d["name"] == "Dealer")

    # 🎯 條件
    return (
        vol > vol5 * 2 and              # 爆量
        close >= high20 and            # 突破
        ma5 > ma10 > ma20 and          # 多頭排列
        close > open_p and             # 紅K
        r > 65 and                     # 強勢RSI
        change > 4 and                 # 強勢漲幅
        strong_k and                   # 不長上影
        foreign > 0 and                # 外資最重要
        (trust > 0 or dealer > 0)      # 至少一個跟
    )


# ===== 掃描 =====
def scan():
    print("🚀 穩定版掃描中...")

    if not market_ok():
        print("⚠️ 大盤不佳，跳過")
        return

    for s in get_stocks():

        if s in notified:
            continue

        try:
            price = get_price(s)
            inst = get_inst(s)

            if is_strong(price, inst):

                t = price[-1]

                msg = f"""🔥 穩定強勢股：{s}

📈 買點：突破 {t["max"]}
🛑 停損：{t["min"]}
💰 現價：{t["close"]}

條件：爆量＋法人＋趨勢確認
"""

                print(msg)
                send_line(msg)

                notified.add(s)

        except Exception as e:
            print("錯誤:", s, e)


# ===== 主程式 =====
while True:
    scan()
    time.sleep(600)
