import pandas as pd
import numpy as np

# Load POI-enriched data
df = pd.read_csv("ghana_properties_poi_enriched.csv")

def get_location_factor(address):
    if not isinstance(address, str):
        return 1.0
    addr = address.lower()
    if any(x in addr for x in ["legon", "osu", "cantonments", "airport"]):
        return 1.8
    elif any(x in addr for x in ["accra", "east legon", "west legon", "dansoman"]):
        return 1.5
    elif any(x in addr for x in ["takoradi", "kumasi", "tema", "ashaiman"]):
        return 1.2
    else:
        return 1.0

# Generate realistic prices
df['location_factor'] = df['address'].apply(get_location_factor)

base_price = (
    df['area_sqm'] * 800 +
    df['bedrooms'] * 5000 +
    df['bathrooms'] * 3000
)

poi_boost = (
    df['schools_nearby'] * 2000 +
    df['hospitals_nearby'] * 1500 +
    df['malls_nearby'] * 3000 +
    df['transit_nearby'] * 1000
)

df['price_realistic'] = (base_price * df['location_factor']) + poi_boost

# Add some noise (-10% to +10%) to simulate market variation
np.random.seed(42)
noise = np.random.uniform(0.9, 1.1, len(df))
df['price'] = (df['price_realistic'] * noise).round()

# Keep price within reasonable bounds
df['price'] = df['price'].clip(lower=1000, upper=200000)

print("✅ Realistic prices generated!")
print(f"New price range: {df['price'].min():,.0f} – {df['price'].max():,.0f}")
print(f"Average price: {df['price'].mean():,.0f}")

# Save
df.to_csv("ghana_properties_realistic_prices.csv", index=False)
print("\n💾 Saved to 'ghana_properties_realistic_prices.csv'")