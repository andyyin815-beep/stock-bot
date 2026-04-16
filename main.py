import requests
import time
from datetime import datetime

TOKEN = "你的TOKEN".strip()
USER_ID = "你的USER_ID".strip()

notified = set()
last_report_date = ""


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


# ===== 大盤 =====
def get_market():
    try:
        url = "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id=TAIEX"
        data = requests.get(url).json()["data"]

        close = data[-1]["close"]
        prev = data[-2]["close"]
        ma20 = sum(d["close"] for d in data[-20:]) / 20

        change = (close - prev) / prev * 100

        return close, ma20, change
    except:
        return 0, 0, 0


def market_ok():
    close, ma20, _ = get_market()
    return close > ma20


# ===== 股票 =====
def get_stocks():
    data = requests.get("https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo").json()["data"]
    return [d["stock_id"] for d in data][:150]


def get_price(s):
    return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={s}").json().get("data", [])


def get_inst(s):
    return requests.get(f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={s}").json().get("data", [])


# ===== 多頭策略 =====
def strong_stock(price, inst):
    if len(price) < 30 or len(inst) < 10:
        return False

    t = price[-1]
    close = t["close"]
    high20 = max(d["close"] for d in price[-20:])
    vol = t["Trading_Volume"]
    vol5 = sum(d["Trading_Volume"] for d in price[-5:]) / 5

    ma5 = sum(d["close"] for d in price[-5:]) / 5
    ma10 = sum(d["close"] for d in price[-10:]) / 10
    ma20 = sum(d["close"] for d in price[-20:]) / 20

    r = rsi(price)

    last3 = inst[-3:]
    foreign = sum(d["buy_sell"] for d in last3 if d["name"] == "Foreign_Investor")

    return (
        vol > vol5 * 2 and
        close >= high20 and
        ma5 > ma10 > ma20 and
        r > 65 and
        foreign > 0
    )


# ===== 空頭逆勢 =====
def anti_fall(price, inst):
    if len(price) < 30 or len(inst) < 10:
        return False

    t = price[-1]
    close = t["close"]
    prev = price[-2]["close"]

    ma20 = sum(d["close"] for d in price[-20:]) / 20

    last3 = inst[-3:]
    foreign = sum(d["buy_sell"] for d in last3 if d["name"] == "Foreign_Investor")

    change = (close - prev) / prev * 100

    return (
        close > ma20 and      # 抗跌
        change > 2 and        # 逆勢上漲
        foreign > 0           # 外資買
    )


# ===== 掃描 =====
def scan():
    print("🚀 掃描中...")

    weak = not market_ok()

    for s in get_stocks():

        if s in notified:
            continue

        try:
            price = get_price(s)
            inst = get_inst(s)

            if weak:
                if anti_fall(price, inst):
                    msg = f"🛡️ 逆勢強股：{s}"
                    send_line(msg)
                    notified.add(s)

            else:
                if strong_stock(price, inst):
                    msg = f"🔥 強勢飆股：{s}"
                    send_line(msg)
                    notified.add(s)

        except:
            continue


# ===== 中午報告 =====
def daily_report():
    global last_report_date

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    if now.hour == 12 and last_report_date != today:

        close, ma20, change = get_market()

        if close > ma20:
            trend = "📈 多頭"
            action = "可積極找買點"
        else:
            trend = "📉 空頭"
            action = "保守 / 找逆勢股"

        msg = f"""📊 今日盤勢報告

指數：{close:.0f}
漲跌：{change:.2f}%

趨勢：{trend}
建議：{action}
"""

        send_line(msg)
        last_report_date = today


# ===== 主程式 =====
while True:
    scan()
    daily_report()
    time.sleep(600)
