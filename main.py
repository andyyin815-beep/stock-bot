import requests
import time
import urllib3

# 關閉 SSL 警告（很重要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 目標股票（台積電）
stock_id = "2330"

def get_stock_price():
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_id}.tw"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://mis.twse.com.tw/"
    }

    try:
        res = requests.get(url, headers=headers, verify=False, timeout=10)
        data = res.json()

        if data.get("msgArray"):
            price = data["msgArray"][0].get("z", "無成交")
            print(f"目前價格: {price}")
        else:
            print("抓不到資料")

    except Exception as e:
        print("錯誤:", e)


# 每60秒抓一次
while True:
    get_stock_price()
    time.sleep(60)
