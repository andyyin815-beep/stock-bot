import requests
import pandas as pd
import numpy as np
import time
import joblib
import warnings

warnings.filterwarnings("ignore")

# ====== 你的 LINE ======
LINE_TOKEN = "ZMvaknwB2/EU4PPjVhls/DCb8dITxVZjDLtbArfPVskXt6unAXNSpQOc1Rv7V/C7rc5QHaOW7lzKSPsBH4t730 tFj6492Gea9+caOScXpU1eHUHrJOa4tcbWdhlJ8l06PEpY1Y71xcI0oYZBeRqk5QdB04t89/1O/w1cDnyilFU="
USER_ID = "Ue4ac469ed010e1cebba684c8cb399ae5"

# ====== LINE通知（已修UTF-8）======
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
    except Exception as e:
        print("LINE錯誤:", e)

# ====== 抓台股價格（修SSL+KeyError）======
def get_price(stock_id):
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"
        res = requests.get(url, timeout=10, verify=False).json()

        if "msgArray" not in res or len(res["msgArray"]) == 0:
            return None

        data = res["msgArray"][0]
        price = float(data.get("z", 0)) if data.get("z") != "-" else None

        return price
    except:
        return None

# ====== 技術指標 ======
def calc_indicators(prices):
    df = pd.DataFrame(prices, columns=["close"])

    df["MA5"] = df["close"].rolling(5).mean()
    df["MA10"] = df["close"].rolling(10).mean()
    df["MA20"] = df["close"].rolling(20).mean()

    # RSI
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    df["MACD"] = ema12 - ema26

    return df

# ====== 模擬歷史價格（AI用）======
def fake_history(price):
    return [price * (1 + np.random.randn() * 0.01) for _ in range(30)]

# ====== 載入AI模型 ======
try:
    model = joblib.load("model.pkl")
    print("✅ AI模型載入成功")
except:
    model = None
    print("⚠️ 沒有AI模型")

# ====== 主掃描 ======
def scan():
    print("🚀 開始掃描...")

    # 台股清單（可擴充）
    stocks = [
        "2330","2317","2454","2382","3037",
        "2603","2609","2615","2376","2327"
    ]

    for stock in stocks:
        price = get_price(stock)

        if price is None:
            continue

        history = fake_history(price)
        df = calc_indicators(history)

        latest = df.iloc[-1]

        # ====== 技術條件 ======
        cond = (
            latest["MA5"] > latest["MA10"] > latest["MA20"] and
            latest["RSI"] > 55 and
            latest["MACD"] > 0
        )

        # ====== AI預測 ======
        ai_score = 0
        if model:
            try:
                X = np.array([[latest["RSI"], latest["MACD"]]])
                ai_score = model.predict_proba(X)[0][1]
            except:
                ai_score = 0

        # ====== 進場條件 ======
        if cond and ai_score > 0.7:
            msg = f"""
🚀 主升段訊號
股票：{stock}
價格：{price}
AI勝率：{round(ai_score*100,1)}%
"""
            print(msg)
            send_line(msg)

# ====== 主程式（不會中斷）======
if __name__ == "__main__":
    while True:
        try:
            scan()
            time.sleep(300)  # 每5分鐘掃一次
        except Exception as e:
            print("錯誤:", e)
            time.sleep(60)
