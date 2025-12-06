import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# 1) Load CSV
df = pd.read_csv("data/metrics.csv")

# 2) Sort by time to be safe
df = df.sort_values(["time_s", "vm_id"]).reset_index(drop=True)

# 3) Simple features (you'll add more later)
features = ["cpu_util", "power_w", "temp_c"]
X = df[features].values
y = df["label"].values

# 4) Unsupervised: Isolation Forest
iso = IsolationForest(contamination=0.2, random_state=42)
anoms = iso.fit_predict(X)  # -1 = anomaly, 1 = normal
iso_scores = iso.decision_function(X)
anoms = (anoms == -1).astype(int)  # 1 = anomaly

# Basic "does it light up during fault" check
print("IsolationForest anomaly rate: ", anoms.mean())

# 5) Supervised: train on first 60% of time, test on last 40% (simulates future)
cut = int(len(df) * 0.6)
X_train, y_train = X[:cut], y[:cut]
X_test, y_test = X[cut:], y[cut:]

rf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
rf.fit(X_train, y_train)
proba = rf.predict_proba(X_test)[:, 1]
pred = (proba >= 0.5).astype(int)

prec, rec, f1, _ = precision_recall_fscore_support(y_test, pred, average="binary", zero_division=0)
auc = roc_auc_score(y_test, proba)
print(f"RandomForest: precision={prec:.3f} recall={rec:.3f} F1={f1:.3f} AUC={auc:.3f}")

# 6) Quick plot to visualize
plt.figure()
plt.plot(df["time_s"][cut:], proba, label="RF fault probability")
plt.plot(df["time_s"][cut:], y_test, label="True label")
plt.xlabel("time (s)")
plt.ylabel("probability / label")
plt.title("Fault probability vs truth (test range)")
plt.legend()
plt.show()
