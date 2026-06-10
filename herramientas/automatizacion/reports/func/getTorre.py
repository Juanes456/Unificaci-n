import pandas as pd

#Funcion para crear una nueva columna "Torre Asignado TCS" que busca el grupo en el archivo de parámetros y le asigna la torre correspondiente
def getTorreAsociado(df, asociadosTCS):
    df = df.merge(
        asociadosTCS[['Column1', 'Torre']],
        left_on='Asignado',
        right_on= 'Column1',
        how='left'
    ).drop(columns=['Column1']).rename(columns={'Torre':'Torre Asignado TCS'})
    return df

#Funcion para crear una nueva columna "Torre Grupos" que busca el grupo en el archivo de parámetros y le asigna la torre correspondiente
def getTorreGrupo (df, grupoHelix):
    df = df.merge(
        grupoHelix[['NOMBRE DEL GRUPO BMC HELIX', 'Torre']],
        left_on='Grupo Asignado',
        right_on='NOMBRE DEL GRUPO BMC HELIX',  
        how='left'
    ).drop(columns=['NOMBRE DEL GRUPO BMC HELIX']).rename(columns={'Torre':'Torre Grupos'})
    df['Torre Grupos'] = df.apply(
        lambda row: row['Torre Grupos'] if (pd.isna(row['Asignado']) or row['Asignado'] == '') else '',
        axis=1
    )
    return df

#Funcion para crear una nueva columna "Torre Informe" que unifica las otras dos columnas "Torre Asignado" y "Torre Grupos" dando prioridad a la columna de Torre Asignado
def getTorreInforme(df):
    df['Torre Informe'] = df.apply(
        lambda row: row['Torre Asignado TCS'] if pd.notna(row['Torre Asignado TCS']) else row['Torre Grupos'] if pd.notna(row['Torre Grupos']) else '',
        axis=1
    ) 
    return df
    
#Funcion para WO y obtener la torre por grupo
def getTorreGrupoWO(group, dfGroupHelix):
    # Filtramos el DataFrame por el nombre del grupo
    dfGroupHelix = dfGroupHelix[dfGroupHelix['NOMBRE DEL GRUPO BMC HELIX'] == group]
    if dfGroupHelix.empty:
        return None
    # Si hay coincidencias, devolvemos la torre asignada
    return dfGroupHelix['Torre'].values[0]