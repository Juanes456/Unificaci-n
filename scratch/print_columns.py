import pandas as pd
file_path = r"c:\Users\3171131\Downloads\Copy of WO y TASK Plataformas Centrales v3 1.xlsx"
df = pd.read_excel(file_path)
print(list(df.columns))
