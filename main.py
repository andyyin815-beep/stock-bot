import requests
import time

TOKEN = "ZMvaknwB2/EU4PPjVhls/DCb8dITxVZjDLtbArfPVskXt6unAXNSpQOc1Rv7V/C7rc5QHaOW7lzKSPsBH4t730 tFj6492Gea9+caOScXpU1eHUHrJOa4tcbWdhlJ8l06PEpY1Y71xcI0oYZBeRqk5QdB04t89/1O/w1cDnyilFU="
USER_ID = "Ue4ac469ed010e1cebba684c8cb399ae5"

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": msg}]
    }
    requests.post(url, headers=headers, json=data)

def check_stock():
    url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw"
    res = requests.get(url).json()
    price = float(res["msgArray"][0]["z"])
    return price

last_price = 0

while True:
    try:
        price = check_stock()
        print("目前價格:", price)

        if last_price != 0:
            change = (price - last_price) / last_price * 100

            if change > 2:
                send_line(f"🚀 飆股警報！上漲 {round(change,2)}% 現價 {price}")

        last_price = price
        time.sleep(60)

    except Exception as e:
        print("錯誤:", e)
        time.sleep(60)
