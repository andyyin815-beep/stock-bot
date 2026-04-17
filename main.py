import requests
import pandas as pd
import numpy as np
import time
import warnings
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore")

# ===== LINE 設定 =====
LINE_TOKEN = "你的LINE_TOKEN"
USER_ID = "你的USER_ID"

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
        requests.post(url, headers=headers, json=payload, timeout=10)
    except:
        pass

# ===== 抓股票資料（穩定版）=====
def get_stock(stock_id):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_id}.TW"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            print(f"{stock_id} 抓資料失敗")
            return None

        data = res.json()

        result = data.get('chart', {}).get('result')

        if not result:
            print(f"{stock_id} 無資料")
            return None

        closes = result[0]['indicators']['quote'][0]['close']
        df = pd.DataFrame({"close": closes})

        return df.dropna()

    except Exception as e:
        print(f"{stock_id} error:", e)
        return None

# ===== 建立資料 =====
def build_data(stock_id):
    df = get_stock(stock_id)

    if df is None or len(df) < 20:
        return None

    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()

    df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)

    df = df.dropna()
    return df

# ===== 訓練模型 =====
def train_model(df):
    X = df[['ma5', 'ma10']]
    y = df['target']

    model = RandomForestClassifier()
    model.fit(X, y)
    return model

# ===== 預測 =====
def predict(stock_id, model):
    df = build_data(stock_id)

    if df is None:
        return None, None

    latest = df.iloc[-1]

    X = [[latest['ma5'], latest['ma10']]]
    pred = model.predict(X)[0]

    return pred, latest['close']

# ===== 主程式 =====
stocks = ["2330", "2317", "2454"]  # 台積電 鴻海 聯發科

print("🚀 開始訓練 AI...")

dfs = []
for s in stocks:
    d = build_data(s)
    if d is not None:
        dfs.append(d)

if len(dfs) == 0:
    print("❌ 沒資料，停止")
    exit()

df_all = pd.concat(dfs)
model = train_model(df_all)

print("✅ AI訓練完成")

# ===== 監控循環 =====
while True:
    print("🔍 掃描中...")

    for s in stocks:
        try:
            pred, price = predict(s, model)

            if pred is None:
                continue

            print(f"{s} 預測: {pred} 價格: {price}")

            if pred == 1:
                send_line(f"🔥 AI買進訊號\n股票: {s}\n現價: {price}")

        except Exception as e:
            print("錯誤:", e)

    time.sleep(300)  # 每5分鐘跑一次
