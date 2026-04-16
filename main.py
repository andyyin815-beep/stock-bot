import requests
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
from xgboost import XGBClassifier
import time

# ===== LINE設定 =====
TOKEN = "你的TOKEN".strip()
USER_ID = "你的USER_ID".strip()

def send_line(msg):
    try:
        requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": "Bearer " + TOKEN,
                "Content-Type": "application/json"
            },
            json={"to": USER_ID, "messages": [{"type": "text", "text": msg}]}
        )
    except:
        pass


# ===== 股票資料 =====
def get_stocks():
    data = requests.get(
        "https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockInfo"
    ).json()["data"]
    return [d["stock_id"] for d in data][:30]


def get_price(s):
    return requests.get(
        f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockPrice&data_id={s}"
    ).json().get("data", [])


# ===== RSI =====
def rsi(prices):
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    if sum(losses[-14:]) == 0:
        return 100

    rs = sum(gains[-14:]) / sum(losses[-14:])
    return 100 - (100 / (1 + rs))


# ===== 建立資料 =====
def build_data(price):
    X_lstm, X_xgb, y = [], [], []

    closes = [d["close"] for d in price]
    vols = [d["Trading_Volume"] for d in price]

    for i in range(30, len(closes)-5):

        # LSTM
        seq = closes[i-30:i]

        # XGB特徵
        ma5 = np.mean(closes[i-5:i])
        ma20 = np.mean(closes[i-20:i])
        vol5 = np.mean(vols[i-5:i])

        feat = [
            closes[i]/ma20,
            ma5/ma20,
            vols[i]/vol5,
            rsi(closes[:i]) / 100
        ]

        future = closes[i+5]
        change = (future - closes[i]) / closes[i]

        X_lstm.append(seq)
        X_xgb.append(feat)
        y.append(1 if change > 0.03 else 0)

    return np.array(X_lstm), np.array(X_xgb), np.array(y)


# ===== LSTM模型 =====
def build_lstm():
    model = tf.keras.Sequential([
        layers.LSTM(64, input_shape=(30,1)),
        layers.Dense(1, activation="sigmoid")
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy")
    return model


# ===== 訓練模型 =====
def train_models():
    print("🧠 訓練模型中...")

    X_lstm_all, X_xgb_all, y_all = [], [], []

    for s in get_stocks():
        price = get_price(s)

        if len(price) < 100:
            continue

        X_lstm, X_xgb, y = build_data(price)

        X_lstm_all.extend(X_lstm)
        X_xgb_all.extend(X_xgb)
        y_all.extend(y)

    X_lstm_all = np.array(X_lstm_all).reshape(-1,30,1)
    X_xgb_all = np.array(X_xgb_all)
    y_all = np.array(y_all)

    lstm = build_lstm()
    lstm.fit(X_lstm_all, y_all, epochs=3, batch_size=32)

    xgb = XGBClassifier()
    xgb.fit(X_xgb_all, y_all)

    return lstm, xgb


# ===== 回測 =====
def backtest(lstm, xgb):
    print("📊 回測中...")

    win, total = 0, 0

    for s in get_stocks():
        price = get_price(s)
        if len(price) < 60:
            continue

        closes = [d["close"] for d in price]
        vols = [d["Trading_Volume"] for d in price]

        for i in range(30, len(closes)-5):

            seq = np.array(closes[i-30:i]).reshape(1,30,1)
            p1 = lstm.predict(seq, verbose=0)[0][0]

            ma5 = np.mean(closes[i-5:i])
            ma20 = np.mean(closes[i-20:i])
            vol5 = np.mean(vols[i-5:i])

            feat = [[
                closes[i]/ma20,
                ma5/ma20,
                vols[i]/vol5,
                rsi(closes[:i])/100
            ]]

            p2 = xgb.predict_proba(feat)[0][1]

            prob = 0.6*p1 + 0.4*p2

            if prob > 0.7:
                total += 1
                future = closes[i+5]
                change = (future - closes[i]) / closes[i]

                if change > 0:
                    win += 1

    if total > 0:
        winrate = win/total*100
        msg = f"📊 回測勝率：{winrate:.2f}%（{total}筆）"
        print(msg)
        send_line(msg)


# ===== 即時選股 =====
def scan(lstm, xgb):
    print("🤖 AI選股中...")

    for s in get_stocks():
        price = get_price(s)

        if len(price) < 30:
            continue

        closes = [d["close"] for d in price]
        vols = [d["Trading_Volume"] for d in price]

        # LSTM
        seq = np.array(closes[-30:]).reshape(1,30,1)
        p1 = lstm.predict(seq, verbose=0)[0][0]

        # XGB
        ma5 = np.mean(closes[-5:])
        ma20 = np.mean(closes[-20:])
        vol5 = np.mean(vols[-5:])

        feat = [[
            closes[-1]/ma20,
            ma5/ma20,
            vols[-1]/vol5,
            rsi(closes)/100
        ]]

        p2 = xgb.predict_proba(feat)[0][1]

        prob = 0.6*p1 + 0.4*p2

        if prob > 0.7:
            msg = f"""🔥 AI強勢股：{s}

勝率：{prob:.2f}
建議：可進場
"""
            print(msg)
            send_line(msg)


# ===== 主程式 =====
lstm, xgb = train_models()
backtest(lstm, xgb)

while True:
    scan(lstm, xgb)
    time.sleep(600)
