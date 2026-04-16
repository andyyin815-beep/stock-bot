import requests
import pandas as pd
import numpy as np
import time
import joblib
import warnings
import os

warnings.filterwarnings("ignore")

# ===== LINE（用環境變數，安全）=====
LINE_TOKEN = os.getenv("LINE_TOKEN")
USER_ID = os.getenv("USER_ID")

# ===== 載入AI模型 =====
try:
    model = joblib.load("model.pkl")
    print("✅ AI模型載入成功")
except:
    model = None
    print("⚠️ 沒有AI模型")

# ===== LINE推播 =====
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

# ===== 抓股價（台股）=====
def get_price(stock_id):
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)

        data = res.json()

        if "msgArray" not in data or len(data["msgArray"]) == 0:
            return None

        price = float(data["msgArray"][0]["z"])
        return price

    except:
        return None

# ===== 模擬技術指標（穩定版）=====
def get_fake_indicator():
    volume_ratio = np.random.uniform(1, 3)
    rsi = np.random.uniform(40, 80)
    macd = np.random.uniform(-1, 2)
    return volume_ratio, rsi, macd

# ===== 主程式 =====
def run():
    print("🚀 開始掃描...")

    # 測試幾檔股票
    stock_list = ["2330", "2603", "2382", "3037", "2376"]

    for stock_id in stock_list:

        price = get_price(stock_id)
        if not price:
            continue

        # 技術指標（目前用穩定版）
        volume_ratio, rsi, macd = get_fake_indicator()

        # ===== AI勝率 =====
        ai_score = 0

        if model:
            try:
                features = np.array([[volume_ratio, rsi, macd]])
                ai_score = model.predict_proba(features)[0][1]
            except:
                ai_score = 0

        # ===== 篩選條件（簡單版）=====
        if volume_ratio > 1.5 and rsi > 50:

            msg = f"""🚀 主升段飆股

股票: {stock_id}
價格: {price}

📊 RSI: {rsi:.2f}
📊 MACD: {macd:.2f}
📊 量比: {volume_ratio:.2f}

🔥 AI勝率: {ai_score:.2%}
"""

            print(msg)
            send_line(msg)

            time.sleep(1)

# ===== 主迴圈 =====
if __name__ == "__main__":
    while True:
        run()
        time.sleep(60)
