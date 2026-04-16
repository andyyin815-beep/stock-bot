import requests
import pandas as pd
import time
import urllib3

# 關閉 SSL 警告（解決 TWSE 問題）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== LINE 設定 =====
LINE_TOKEN = "你的LINE_TOKEN"
USER_ID = "你的USER_ID"


# ===== LINE 推播 =====
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
        r = requests.post(url, headers=headers, json=data, timeout=5)
        print("LINE發送:", r.status_code)
    except Exception as e:
        print("LINE錯誤:", e)


# ===== 抓股價（穩定版）=====
def get_price(stock_id):
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"

    try:
        res = requests.get(url, timeout=5, verify=False)
        data = res.json()

        # 防呆
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
        print(f"{stock_id} 抓價錯誤:", e)
        return None


# ===== 技術指標（簡化版）=====
def calc_signal(price):
    # 先用簡單條件（後面可升級AI）
    if price > 100:
        return True
    return False


# ===== 掃描股票 =====
def scan():
    print("🚀 掃描中...")

    # 👉 可自己擴充
    stocks = [
        "2330", "2317", "2454",
        "2382", "2303", "2603",
        "3037", "2376", "2327"
    ]

    for stock in stocks:
        price = get_price(stock)

        if price is None:
            continue

        print(f"{stock} 價格: {price}")

        if calc_signal(price):
            msg = f"🚀【主升段訊號】\n股票: {stock}\n價格: {price}"
            print(msg)
            send_line(msg)


# ===== 主程式（永不當機版）=====
while True:
    try:
        scan()

        # 每60秒掃一次
        time.sleep(60)

    except Exception as e:
        print("🔥主程式錯誤:", e)
        time.sleep(10)
