import requests
import pandas as pd
import time

# ===== LINE 推播 =====
LINE_TOKEN = "你的TOKEN"
USER_ID = "你的USER_ID"

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }
    try:
        requests.post(url, headers=headers, json=data)
    except:
        print("LINE 發送失敗")


# ===== 安全抓價格 =====
def get_price(stock_id):
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"

    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        # 🔥 重點：防呆
        if "msgArray" not in data:
            print(f"{stock_id} 無資料")
            return None

        if len(data["msgArray"]) == 0:
            print(f"{stock_id} 空資料")
            return None

        price = data["msgArray"][0].get("z", "-")

        if price == "-" or price == "":
            return None

        return float(price)

    except Exception as e:
        print("抓價錯誤:", e)
        return None


# ===== 簡單AI條件（你後面再升級）=====
def check_signal(stock_id):
    price = get_price(stock_id)

    if price is None:
        return None

    # 👉 範例條件（你之後會用AI取代）
    if price > 100:
        return f"🚀 {stock_id} 突破訊號！價格：{price}"

    return None


# ===== 主掃描 =====
def scan():
    stocks = ["2330", "2317", "2454", "2603", "2382"]

    print("🚀 掃描中...")

    for s in stocks:
        signal = check_signal(s)
        if signal:
            print(signal)
            send_line(signal)


# ===== 主程式（防當機版）=====
while True:
    try:
        scan()
        time.sleep(60)

    except Exception as e:
        print("主程式錯誤:", e)
        time.sleep(10)
