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
        requests.post(url, headers=headers, json=payload, timeout=10)
    except:
        pass

# ===== 抓資料（含高低）=====
def get_stock(stock_id):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_id}.TW"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        result = data.get('chart', {}).get('result')
        if not result:
            return None

        quote = result[0]['indicators']['quote'][0]

        df = pd.DataFrame({
            "close": quote['close'],
            "high": quote['high'],
            "low": quote['low'],
            "volume": quote['volume']
        })

        return df.dropna()

    except:
        return None

# ===== 建資料 =====
def build_data(stock_id):
    df = get_stock(stock_id)

    if df is None or len(df) < 50:
        return None

    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['vol_ma5'] = df['volume'].rolling(5).mean()

    df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)

    df = df.dropna()
    return df

# ===== 訓練 =====
def train_model(df):
    X = df[['ma5', 'ma10', 'ma20']]
    y = df['target']

    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)
    return model

# ===== 主力吸籌 =====
def is_accumulating(df):
    last5 = df['close'].iloc[-5:]

    up_days = sum(last5.diff() > 0)
    return up_days >= 3

# ===== 假突破過濾 =====
def is_fake_breakout(df):
    latest = df.iloc[-1]

    body = abs(latest['close'] - latest['low'])
    total = latest['high'] - latest['low']

    if total == 0:
        return True

    # 收盤在低檔 = 弱
    return (body / total) < 0.3

# ===== 強訊號 =====
def check_signal(df, model):
    latest = df.iloc[-1]

    # AI
    X = [[latest['ma5'], latest['ma10'], latest['ma20']]]
    ai = model.predict(X)[0]

    # 趨勢
    trend = latest['ma5'] > latest['ma10'] > latest['ma20']

    # 突破20日
    breakout = latest['close'] > df['close'].rolling(20).max().iloc[-2]

    # 量
    volume = latest['volume'] > latest['vol_ma5'] * 1.5

    # 主力
    acc = is_accumulating(df)

    # 假突破
    fake = is_fake_breakout(df)

    return ai, trend, breakout, volume, acc, fake, latest['close']

# ===== 主程式 =====
stocks = ["2330", "2317", "2454"]

print("🚀 訓練AI中...")

dfs = []
for s in stocks:
    d = build_data(s)
    if d is not None:
        dfs.append(d)

if len(dfs) == 0:
    print("❌ 沒資料")
    exit()

df_all = pd.concat(dfs)
model = train_model(df_all)

print("✅ AI完成")

# ===== 監控 =====
while True:
    print("🔍 掃描中...")

    for s in stocks:
        try:
            df = build_data(s)
            if df is None:
                continue

            ai, trend, breakout, vol, acc, fake, price = check_signal(df, model)

            print(f"{s} AI:{ai} 趨勢:{trend} 突破:{breakout} 量:{vol} 主力:{acc} 假突破:{fake}")

            if ai == 1 and trend and breakout and vol and acc and not fake:
                send_line(
                    f"🚀 終極買點\n"
                    f"股票: {s}\n"
                    f"價格: {price}\n"
                    f"條件: AI+多頭+突破+爆量+主力+無假突破"
                )

        except Exception as e:
            print("錯誤:", e)

    time.sleep(300)
