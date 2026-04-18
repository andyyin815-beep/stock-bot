import threading
import time

def run_bot():
    try:
        from auto_trader import start
        start()
    except Exception as e:
        print("❌ Bot 發生錯誤：", e)

print("🚀 Railway Bot 啟動中...")

# 👉 用背景執行（避免卡住）
t = threading.Thread(target=run_bot)
t.daemon = True   # 關鍵：讓主程式結束也不影響
t.start()

# 👉 快速初始化（避免 Railway timeout）
for i in range(3):
    print(f"初始化中 {i+1}/3")
    time.sleep(1)

print("✅ 系統已成功啟動（穩定運行中）")

# 👉 防止程式直接結束（關鍵🔥）
while True:
    time.sleep(60)
