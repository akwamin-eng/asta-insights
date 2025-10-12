# preprocess.py
import pandas as pd
import numpy as np

def parse_size_to_sqm(size_val):
    """Convert size (text or number) to square meters. Assumes input is in sq ft."""
    try:
        # Handle both string and numeric
        if pd.isna(size_val):
            return np.nan
        value = float(size_val)
        # Convert sq ft to sq m
        return value * 0.092903
    except (ValueError, TypeError):
        return np.nan

def preprocess_data(df):
    df = df.copy()
    df['area_sqm'] = df['size'].apply(parse_size_to_sqm)
    
    # Only remove rows where area_sqm is missing or <= 0
    df = df[df['area_sqm'].notna() & (df['area_sqm'] > 0)]
    
    # Keep reasonable prices (GHS 500 to 200,000)
    df = df[(df['price'] >= 500) & (df['price'] <= 200000)]
    
    # Add price per sqm
    df['price_per_sqm'] = df['price'] / df['area_sqm']
    
    return df

# Load and preprocess
df_raw = pd.read_csv("ghana_properties_raw.csv")
print(f"Starting with {len(df_raw)} properties")

df_clean = preprocess_data(df_raw)

print(f"After cleaning: {len(df_clean)} properties")
if len(df_clean) > 0:
    print(f"Area range: {df_clean['area_sqm'].min():.1f} – {df_clean['area_sqm'].max():.1f} sqm")
    df_clean.to_csv("ghana_properties_clean.csv", index=False)
    print("✅ Cleaned data saved to 'ghana_properties_clean.csv'")
else:
    print("❌ No valid properties after cleaning. Check 'size' and 'price' values.")