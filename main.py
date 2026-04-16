import requests
import time
import urllib3

# ===== 關閉 SSL 警告（解決台股API問題）=====
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== LINE 設定（自己填）=====
LINE_TOKEN = "你的LINE_TOKEN"
USER_ID = "你的USER_ID"


# ===== LINE 推播（已修 encoding 問題）=====
def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }

    data = {
        "to": USER_ID,
        "messages": [
            {
                "type": "text",
                "text": msg
            }
        ]
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
            return None

        if len(data["msgArray"]) == 0:
            return None

        price = data["msgArray"][0].get("z", "-")

        if price == "-" or price == "":
            return None

        return float(price)

    except Exception as e:
        print(f"{stock_id} 抓價錯誤:", e)
        return None


# ===== 訊號判斷（基礎版）=====
def check_signal(stock_id):
    price = get_price(stock_id)

    if price is None:
        return None

    print(f"{stock_id} 價格: {price}")

    # 👉 基本突破條件（可升級）
    if price > 100:
        return f"【主升段訊號】\n股票: {stock_id}\n價格: {price}"

    return None


# ===== 掃描股票 =====
def scan():
    print("🚀 掃描中...")

    stocks = [
        "2330", "2317", "2454",
        "2382", "2303", "2603",
        "3037", "2376", "2327"
    ]

    for stock in stocks:
        signal = check_signal(stock)

        if signal:
            print(signal)
            send_line(signal)


# ===== 主程式（防當機）=====
while True:
    try:
        scan()

        # 每60秒掃一次
        time.sleep(60)

    except Exception as e:
        print("🔥主程式錯誤:", e)
        time.sleep(10)
