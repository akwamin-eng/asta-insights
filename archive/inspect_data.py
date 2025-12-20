import pandas as pd

df = pd.read_csv("ghana_properties_raw.csv")
print("Sample 'size' values:")
print(df['size'].value_counts().head(10))

print("\nSample 'address' values:")
print(df['address'].head(10))
