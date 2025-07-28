import pandas as pd
import joblib
import shap
import json
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# --- 1. Load and prepare data ---
df = pd.read_excel("myexc1.xlsx", sheet_name="Orders")
df = df[df["Profit"].notnull()]  # Drop rows with missing target

features = ["Category", "Sub-Category", "Segment", "Region", "Sales", "Discount", "Quantity"]
X_raw = df[features]
y = df["Profit"]

# One-hot encoding of categoricals
X = pd.get_dummies(X_raw, drop_first=True)

# --- 2. Train/test split ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# --- 3. Train XGBoost regressor ---
model = XGBRegressor(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    objective="reg:squarederror",
    random_state=42
)
model.fit(X_train, y_train)

# --- 4. Evaluate ---
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred)
print(f"R² Score: {r2:.3f}")
print(f"RMSE: {rmse:.2f}")

# --- 5. Save model and feature names ---
joblib.dump(model, "models/profit_regressor_xgb.joblib")
with open("models/profit_feature_names.json", "w") as f:
    json.dump(list(X.columns), f)

# --- 6. SHAP feature importance summary ---
explainer = shap.Explainer(model, X)
shap_values = explainer(X)

shap_df = pd.DataFrame({
    "feature": X.columns,
    "importance": shap_values.abs.mean(0).values
}).sort_values(by="importance", ascending=False).head(10)

shap_df.to_csv("models/shap_profit_top_features.csv", index=False)
print("SHAP feature importance saved: models/shap_profit_top_features.csv")
