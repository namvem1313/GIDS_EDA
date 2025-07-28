import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import json

# --- 1. Load and preprocess your dataset ---
df = pd.read_excel("myexc1.xlsx", sheet_name="Orders")  # or use merged df
df["Return_Flag"] = df["Return"].apply(lambda x: 1 if x == "Yes" else 0)

features = ["Category", "Sub-Category", "Segment", "Region", "Sales", "Discount"]
X_raw = df[features]
y = df["Return_Flag"]

# One-hot encode categorical variables
X = pd.get_dummies(X_raw, drop_first=True)

# --- 2. Apply SMOTE ---
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X, y)

# --- 3. Train XGBoost model ---
scale_weight = (y == 0).sum() / (y == 1).sum()

model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    objective='binary:logistic',
    scale_pos_weight=scale_weight,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)
model.fit(X_resampled, y_resampled)

# --- 4. Evaluate and print report (optional) ---
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

# --- 5. Save model ---
joblib.dump(model, "models/return_classifier_xgboost.joblib")
print("Model saved as models/return_classifier_xgboost.joblib")

# Save feature names separately (as .json or .txt)
feature_names = list(X.columns)
with open("models/xgboost_feature_names.json", "w") as f:
    json.dump(feature_names, f)
print("Feature names saved as models/xgboost_feature_names.json")

# --- 6. SHAP Feature Importance Summary (Optional) ---
explainer = shap.Explainer(model, X)
shap_values = explainer(X)

# Save top 10 features (avg absolute SHAP value)
shap_df = pd.DataFrame({
    "feature": X.columns,
    "importance": shap_values.abs.mean(0).values
}).sort_values(by="importance", ascending=False).head(10)

shap_df.to_csv("models/shap_top_features.csv", index=False)
print("SHAP top features saved to models/shap_top_features.csv")