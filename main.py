import requests
import time

TOKEN = "你的TOKEN"
USER_ID = "你的USER_ID"


def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }
    requests.post(url, headers=headers, json=data)


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


def market_ok():
    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=TAIEX"
        data = requests.get(url).json()["data"]

        close = data[-1]["close"]
        ma20 = sum(d["close"] for d in data[-20:]) / 20

        return close > ma20
    except:
        return False


def get_all_stocks():
    data = requests.get("https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo").json()["data"]
    return [d["stock_id"] for d in data][:200]


def get_price(s):
    try:
        return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={s}").json()["data"]
    except:
        return []


def get_inst(s):
    try:
        return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={s}").json()["data"]
    except:
        return []


def is_hot(price, inst):
    if len(price) < 30 or len(inst) < 10:
        return False

    t = price[-1]

    close = t["close"]
    high = t["max"]
    low = t["min"]
    open_p = t["open"]
    vol = t["Trading_Volume"]

    if vol < 2000:
        return False

    vol5 = sum(d["Trading_Volume"] for d in price[-5:]) / 5
    ma5 = sum(d["close"] for d in price[-5:]) / 5
    ma10 = sum(d["close"] for d in price[-10:]) / 10
    ma20 = sum(d["close"] for d in price[-20:]) / 20
    high20 = max(d["close"] for d in price[-20:])

    rsi = calculate_rsi(price)

    last3 = inst[-3:]
    foreign = sum(d["buy_sell"] for d in last3 if d["name"] == "Foreign_Investor")
    trust = sum(d["buy_sell"] for d in last3 if d["name"] == "Investment_Trust")
    dealer = sum(d["buy_sell"] for d in last3 if d["name"] == "Dealer")

    change = (close - price[-2]["close"]) / price[-2]["close"] * 100
    strong = close >= high * 0.9

    return (
        vol > vol5 * 2 and
        close >= high20 and
        ma5 > ma10 > ma20 and
        close > open_p and
        rsi > 60 and
        change > 3 and
        strong and
        foreign > 0 and trust > 0 and dealer > 0
    )


def scan():
    print("🚀 掃描中...")

    if not market_ok():
        msg = "⚠️ 大盤偏弱，今日觀望"
        print(msg)
        send_line(msg)
        return

    found = False

    for s in get_all_stocks():
        price = get_price(s)
        inst = get_inst(s)

        if is_hot(price, inst):
            found = True
            t = price[-1]

            msg = f"""🔥 主力法人股：{s}

📈 買點：突破 {t["max"]}
🛑 停損：{t["min"]}
🎯 策略：突破買
"""
            print(msg)
            send_line(msg)

    if not found:
        print("❌ 今日無訊號")


while True:
    scan()
    time.sleep(600)
