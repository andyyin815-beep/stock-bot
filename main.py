import requests
import numpy as np
import joblib
import time

# ===== LINE 設定 =====
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
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print("LINE錯誤:", e)

# ===== 載入AI模型 =====
model = joblib.load("model.pkl")

def predict(features):
    weights = model["weights"]
    threshold = model["threshold"]

    score = sum(f*w for f, w in zip(features, weights))
    return score

# ===== 假資料（之後可接真API）=====
def get_fake_data():
    vol = np.random.rand()
    foreign = np.random.rand()
    main = np.random.rand()
    return [vol, foreign, main]

# ===== 主程式 =====
print("🚀 AI飆股獵人啟動")

while True:
    try:
        features = get_fake_data()
        score = predict(features)

        print("分數:", round(score, 3))

        if score > 0.65:
            msg = f"🔥 AI抓到飆股機會！\n分數: {round(score,3)}"
            send_line(msg)

        time.sleep(10)

    except Exception as e:
        print("錯誤:", e)
        time.sleep(10)
