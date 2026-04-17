import requests
import pandas as pd
import numpy as np
import time
import warnings
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore")

# ===== LINE =====
LINE_TOKEN = "ZMvaknwB2/EU4PPjVhls/DCb8dITxVZjDLtbArfPVskXt6unAXNSpQOc1Rv7V/C7rc5QHaOW7lzKSPsBH4t730 tFj6492Gea9+caOScXpU1eHUHrJOa4tcbWdhlJ8l06PEpY1Y71xcI0oYZBeRqk5QdB04t89/1O/w1cDnyilFU="
USER_ID = "Ue4ac469ed010e1cebba684c8cb399ae5"

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }
    try:
        requests.post(url, headers=headers, json=payload)
    except:
        pass

# ===== 抓台股資料（Yahoo）=====
def get_stock(stock_id):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_id}.TW"
    res = requests.get(url)
    data = res.json()

    closes = data['chart']['result'][0]['indicators']['quote'][0]['close']
    df = pd.DataFrame({"close": closes})
    return df

# ===== 建資料 =====
def build_data(stock_id):
    df = get_stock(stock_id)

    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()

    df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)

    df = df.dropna()
    return df

# ===== 訓練 AI =====
def train_model(df):
    X = df[['ma5', 'ma10']]
    y = df['target']

    model = RandomForestClassifier()
    model.fit(X, y)
    return model

# ===== 預測 =====
def predict(stock_id, model):
    df = build_data(stock_id)
    latest = df.iloc[-1]

    X = [[latest['ma5'], latest['ma10']]]
    pred = model.predict(X)[0]

    return pred, latest['close']

# ===== 主程式 =====
stocks = ["2330", "2317", "2454"]

print("🚀 開始訓練 AI...")

df_all = pd.concat([build_data(s) for s in stocks])
model = train_model(df_all)

print("✅ AI訓練完成")

while True:
    for s in stocks:
        try:
            pred, price = predict(s, model)

            if pred == 1:
                send_line(f"🔥 AI買進訊號 {s} 現價 {price}")

        except Exception as e:
            print("錯誤:", e)

    time.sleep(300)
