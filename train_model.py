import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

# Load cleaned data
df = pd.read_csv("ghana_properties_clean.csv")

# Remove extremely small areas (likely data errors)
df = df[df['area_sqm'] >= 10]  # at least 10 sqm
print(f"Using {len(df)} properties for training (area >= 10 sqm)")

# Prepare features
features = ['bedrooms', 'bathrooms', 'area_sqm', 'latitude', 'longitude']
X = df[features].copy()
y = np.log1p(df['price'])  # log-transform price for better modeling

# Handle any remaining missing values
X = X.fillna(X.median())

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
print("Training XGBoost model...")
model = xgb.XGBRegressor(
    n_estimators=300,
    learning_rate=0.1,
    max_depth=6,
    subsample=0.8,
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mae = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred))
r2 = r2_score(y_test, y_pred)

print(f"\n✅ Model Performance:")
print(f" - R²: {r2:.3f}")
print(f" - MAE: GHS {mae:,.0f}")

# Generate predictions for ALL properties
df['predicted_price'] = np.expm1(model.predict(X))
df['price_diff_pct'] = (df['predicted_price'] - df['price']) / df['price']

# Save results
df.to_csv("ghana_properties_with_predictions.csv", index=False)
print("\n💾 Predictions saved to 'ghana_properties_with_predictions.csv'")