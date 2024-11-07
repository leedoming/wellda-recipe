import pandas as pd
df = pd.read_csv("../data/dw_recipes_fin1.csv")
print("전체 컬럼 목록:")
for col in df.columns:
    print(f"- {col}")