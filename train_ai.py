import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import joblib

print("🚀 開始訓練AI...")

# 模擬資料（避免API問題）
X = np.random.rand(1000, 3)
y = (X[:, 0] + X[:, 1] * 0.5 > 0.8).astype(int)

# 切分資料
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 建立模型
model = XGBClassifier()
model.fit(X_train, y_train)

# 存模型
joblib.dump(model, "model.pkl")

print("✅ AI模型訓練完成")