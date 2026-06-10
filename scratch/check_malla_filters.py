import pandas as pd

file_path = r"C:\Users\3171131\Desktop\excels\WO y TASK Plataformas Centrales v3 8.xlsx"
df = pd.read_excel(file_path)

# Filter by Oferta
df_oferta = df[df["Oferta"].astype(str).str.strip().str.lower() == "respaldos de información en servidores"]
print(f"1. Rows with Oferta='Respaldos de información en servidores': {len(df_oferta)}")

# Filter by TipoSolicitud
col_tipo_solicitud = "TipoSolicitud"
df_tipo = df_oferta[df_oferta[col_tipo_solicitud].str.contains("Creación", na=False)]
print(f"2. Rows after TipoSolicitud contains 'Creación': {len(df_tipo)}")
if len(df_tipo) == 0:
    print("Unique values of TipoSolicitud in Oferta:")
    print(df_oferta[col_tipo_solicitud].value_counts(dropna=False))

# Filter by Descripción
col_descripcion = "Descripción"
df_desc = df_tipo[
    df_tipo[col_descripcion]
    .astype(str)
    .str.lower()
    .str.contains(r"tipo solicitud.*cre", regex=True, na=False)
]
print(f"3. Rows after Descripción regex 'tipo solicitud.*cre': {len(df_desc)}")
if len(df_desc) == 0 and len(df_tipo) > 0:
    print("Sample descriptions in these rows:")
    for d in df_tipo[col_descripcion].head(5):
        print("  -", repr(d))
