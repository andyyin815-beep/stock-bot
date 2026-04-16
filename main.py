import requests
import time
from datetime import datetime

TOKEN = "你的TOKEN".strip()
USER_ID = "你的USER_ID".strip()

notified = set()

# ===== LINE =====
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
        requests.post(url, headers=headers, json=data)
    except:
        pass


# ===== 族群（可自己擴充）=====
SECTORS = {
    "AI": ["2330","2382","2308","6669","3231"],
    "軍工": ["4576","8033","2634"],
    "電子": ["2317","2454","2303","2324"]
}


def get_sector(stock_id):
    for k, v in SECTORS.items():
        if stock_id in v:
            return k
    return "其他"


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


# ===== 資料 =====
def get_stocks():
    data = requests.get("https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo").json()["data"]
    return [d["stock_id"] for d in data][:150]


def get_price(s):
    return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={s}").json().get("data", [])


def get_inst(s):
    return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={s}").json().get("data", [])


# ===== 🎯 主升段評分 =====
def score_stock(price, inst):

    if len(price) < 30 or len(inst) < 10:
        return 0

    t = price[-1]

    close = t["close"]
    prev = price[-2]["close"]
    vol = t["Trading_Volume"]

    ma5 = sum(d["close"] for d in price[-5:]) / 5
    ma10 = sum(d["close"] for d in price[-10:]) / 10
    ma20 = sum(d["close"] for d in price[-20:]) / 20

    vol5 = sum(d["Trading_Volume"] for d in price[-5:]) / 5

    r = rsi(price)

    last3 = inst[-3:]
    foreign = sum(d["buy_sell"] for d in last3 if d["name"] == "Foreign_Investor")

    change = (close - prev) / prev * 100

    score = 0

    # 📈 主升段條件
    if close > ma20: score += 2
    if ma5 > ma10 > ma20: score += 2
    if vol > vol5 * 1.8: score += 2
    if r > 60: score += 1
    if change > 3: score += 1
    if foreign > 0: score += 2

    return score


# ===== 掃描 =====
def scan():

    print("🚀 主升段掃描中...")

    candidates = []

    for s in get_stocks():

        if s in notified:
            continue

        try:
            price = get_price(s)
            inst = get_inst(s)

            score = score_stock(price, inst)

            if score >= 6:  # 🔥 門檻（可調）
                candidates.append((s, score, price[-1]["close"]))

        except:
            continue

    # ===== 排名 =====
    candidates.sort(key=lambda x: x[1], reverse=True)

    top = candidates[:5]  # 🔥 只取前5名

    for s, score, price in top:

        sector = get_sector(s)

        msg = f"""🔥 主升段強股：{s}

🏆 分數：{score}/10
📊 族群：{sector}
💰 現價：{price}

策略：主升段起漲
"""

        print(msg)
        send_line(msg)

        notified.add(s)


# ===== 主程式 =====
while True:
    scan()
    time.sleep(600)
