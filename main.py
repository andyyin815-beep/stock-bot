import requests
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import datetime
import time

# ===== LINE =====
TOKEN = "你的TOKEN"
USER_ID = "你的USER_ID"

def send_line(msg):
    requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json"
        },
        json={"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
    )

# ===== 股票清單 =====
stocks = ["2330", "2317", "2454", "2303", "2603", "2609"]

# ===== FinMind 抓資料 =====
def get_price(stock):
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={stock}"
    data = requests.get(url).json()["data"]
    return pd.DataFrame(data)

# ===== 三大法人 =====
def get_institution(stock):
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInstitutionalInvestorsBuySell&data_id={stock}"
    data = requests.get(url).json()["data"]
    df = pd.DataFrame(data)

    foreign = df[df["name"] == "Foreign_Investor"]["buy_sell"].sum()
    return foreign

# ===== RSI =====
def RSI(series, n=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(n).mean()
    loss = -delta.clip(upper=0).rolling(n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ===== MACD =====
def MACD(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

# ===== 主升段判斷 =====
def is_breakout(df):
    ma20 = df["close"].rolling(20).mean()
    today = df.iloc[-1]
    yesterday = df.iloc[-2]

    return (
        today["close"] > ma20.iloc[-1] and
        yesterday["close"] < ma20.iloc[-2]
    )

# ===== 建立訓練資料 =====
def build_data(df):
    X, y = [], []

    for i in range(30, len(df)-5):

        price = df["close"].iloc[i]
        future = df["close"].iloc[i+5]

        rsi = RSI(df["close"]).iloc[i]
        macd, signal = MACD(df["close"])
        macd_val = macd.iloc[i]

        X.append([price, rsi, macd_val])
        y.append(1 if (future - price)/price > 0.03 else 0)

    return np.array(X), np.array(y)

# ===== 訓練AI =====
def train_model():
    X_all, y_all = [], []

    for s in stocks:
        df = get_price(s)
        if len(df) < 100:
            continue

        X, y = build_data(df)
        X_all.extend(X)
        y_all.extend(y)

    model = XGBClassifier()
    model.fit(np.array(X_all), np.array(y_all))

    return model

# ===== 回測 =====
def backtest(model):
    win, total = 0, 0

    for s in stocks:
        df = get_price(s)

        X, y = build_data(df)

        for i in range(len(X)):
            prob = model.predict_proba([X[i]])[0][1]

            if prob > 0.7:
                total += 1
                if y[i] == 1:
                    win += 1

    if total > 0:
        rate = win / total * 100
        msg = f"📊 回測勝率：{rate:.2f}%（{total}筆）"
        print(msg)
        send_line(msg)

# ===== 族群 =====
sector_map = {
    "2330": "AI",
    "2317": "AI",
    "2454": "AI",
    "2303": "半導體",
    "2603": "航運",
    "2609": "航運"
}

# ===== 分析 =====
def analyze(model, stock):
    df = get_price(stock)

    if len(df) < 30:
        return None

    close = df["close"]
    price = close.iloc[-1]

    rsi = RSI(close).iloc[-1]
    macd, signal = MACD(close)

    foreign = get_institution(stock)

    features = [[price, rsi, macd.iloc[-1]]]
    prob = model.predict_proba(features)[0][1]

    # 條件
    if (
        prob > 0.7 and
        rsi < 70 and
        macd.iloc[-1] > signal.iloc[-1] and
        foreign > 0 and
        is_breakout(df)
    ):
        return f"""
🚀【主升段起漲】
股票：{stock}
族群：{sector_map.get(stock, "其他")}

現價：{price}
AI勝率：{prob:.2f}

法人：買超
技術：轉強

👉 買點：{round(price*1.01,2)}
🛑 停損：{round(price*0.97,2)}
"""

# ===== 主程式 =====
model = train_model()
backtest(model)

while True:
    print("🚀 掃描中...")

    for s in stocks:
        result = analyze(model, s)
        if result:
            print(result)
            send_line(result)

    time.sleep(600)
