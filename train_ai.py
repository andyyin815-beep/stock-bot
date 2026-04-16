import numpy as np
import joblib

# 建立訓練資料（模擬）
X = []
y = []

for i in range(300):
    vol = np.random.rand()        # 成交量
    foreign = np.random.rand()    # 外資
    main = np.random.rand()       # 主力

    score = vol*0.4 + foreign*0.3 + main*0.3

    X.append([vol, foreign, main])
    y.append(1 if score > 0.6 else 0)

# 簡單AI模型（權重）
model = {
    "weights": [0.4, 0.3, 0.3],
    "threshold": 0.6
}

# 存檔
joblib.dump(model, "model.pkl")

print("✅ AI模型建立完成")
