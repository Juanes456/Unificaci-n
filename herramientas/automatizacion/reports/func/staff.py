import pandas as pd
import reports.func.getTorre as gT

def staffFilter(df, parameters, dateReport):
    '''
    Validamos que el personal asignado estuviese activo en la torre en el mes de inicio la tarea
    
    input:
    df: DataFrame de los datos de ambos bancos
    parameters: la hoja de Asosicados de TCS del archivo de parametros
    
    return:
    df: DataFrame con la columna "Eliminar" que indica si el personal estaba activo o no en la fecha de inicio de la tarea
    '''
    #Unificamos los colunas del personal de TCS y la torre asignada en el archivo de parametros
    df = gT.getTorreAsociado(df, parameters)
    
    #Damos el formato correcto a las fechas de los parametros y los datos en las columnas de las fechas de retiro del personal y de fecha de inicio de la tarea
    df['Hora Inicio Tarea'] = pd.to_datetime(df['Hora Inicio Tarea'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    parameters['Fecha Retiro de la Torre (DD/MM/AAAA)'] = pd.to_datetime(parameters['Fecha Retiro de la Torre (DD/MM/AAAA)'], format='%d/%m/%Y', errors='coerce')
    
    #Determinamos la fecha de hace un mes atras, con el fin de saber si el personal estaba activo en la torre en el mes de inicio de la tarea
    lastDate = pd.to_datetime(dateReport) - pd.DateOffset(months=1)
    
    #Filtramos el dataframe de parametros para obtener solo los empleados cuya fecha de retiro sea mayor o igual a la fecha de un mes atras
    dfActive = parameters[
        parameters['Fecha Retiro de la Torre (DD/MM/AAAA)'].notna() & 
        (parameters['Fecha Retiro de la Torre (DD/MM/AAAA)'] >= lastDate)
    ]
    
    #Quitamos los asteristos de cada elemento de 'Column1' en dfActive y nos quedamos con las columnas de interes
    dfActive.loc[: , 'Column1'] = dfActive['Column1'].apply(
        lambda x: x if not "*" in str(x) else str(x).replace("*", "")
    )
    dfActive = dfActive[['Column1', 'Fecha Retiro de la Torre (DD/MM/AAAA)', 'Torre']]
    
    #Trabajamos solo con las filas de los datos que tienen asociados asignado
    dataFiltered = df[df['Asignado'].notna()].copy()
    dataFiltered['__idx_original'] = dataFiltered.index
    dataFiltered = pd.merge(
        dataFiltered, 
        dfActive,
        left_on='Asignado', 
        right_on='Column1', 
        how='left'
    )
    
    dataFiltered['Torre Asignado TCS'] = dataFiltered.apply(eleccionTorre, axis=1)
    dataFiltered = dataFiltered.drop(columns=['Column1', 'Fecha Retiro de la Torre (DD/MM/AAAA)', 'Torre'])
    dataFiltered = dataFiltered.drop_duplicates(subset=['__idx_original'])
    dataFiltered = dataFiltered.set_index('__idx_original')
    df.loc[dataFiltered.index, 'Torre Asignado TCS'] = dataFiltered['Torre Asignado TCS']    
    return df

#Función para determinar la Torre del asignado dependiendo de la fecha de retiro
def eleccionTorre(row):
    # Si no hay coincidencia, deja el valor original
    if pd.isna(row['Column1']):
        return row['Torre Asignado TCS']
    # Si la fecha de retiro del personal es mayor a la hora de inicio asigna la torre
    elif pd.notna(row['Hora Inicio Tarea']) and pd.notna(row['Fecha Retiro de la Torre (DD/MM/AAAA)']):
        if (row['Column1'] == row['Asignado']) and (row['Hora Inicio Tarea'] <= row['Fecha Retiro de la Torre (DD/MM/AAAA)'] ):
            return row['Torre']

def normalizeText(text):
    if pd.isna(text):
        return text
    return str(text).replace("*", "").strip().lower()

#Definimos una función especial para las WO
def staffFilterWO(row, dfAssociate, columnDate, columnAssigned):
    '''
        Esta función filtra el personal asignado a las WOs teniendo en cuenta la fecha de retiro del personal y la fecha de cierre de la tarea o WO.
        
        parameters:
            row: La fila del DataFrame que se está procesando
            dfAssociate: DataFrame de los parámetros que contiene la fecha de retiro del personal y la torre asignada
            columnDate: Nombre de la columna que contiene la fecha de cierre de la tarea o WO
            columnAssigned: Nombre de la columna que contiene el personal asignado
        return:
            str: La torre asignada al personal o None si no se cumple la condición
    '''
    
    #Filtramos el Dataframe por nombre del personal asignado
    # dfAssociate = dfAssociate[dfAssociate['Nombre'] == row[columnAssigned]]
    dfAssociate['Nombre_norm'] = dfAssociate['Nombre'].apply(normalizeText)
    dfAssociate = dfAssociate[dfAssociate['Nombre_norm'] == normalizeText(row[columnAssigned])]
    
    if dfAssociate.empty:
        return None
    
    elif len(dfAssociate) == 1:
        # Si hay una sola coincidencia, devolvemos la torre asignada
        return dfAssociate['Torre'].values[0]
    
    # Si hay más de una coincidencia, verificamos la fecha de retiro, para ello damos formato a las fechas de retiro y de cierre de la tarea o WO
    dfAssociate['Fecha Retiro de la Torre (DD/MM/AAAA)'] = pd.to_datetime(
        dfAssociate['Fecha Retiro de la Torre (DD/MM/AAAA)'], 
        format='%d/%m/%Y',
        errors='coerce'
    )
    row[columnDate] = pd.to_datetime(row[columnDate], format='%d/%m/%Y %I:%M:%S %p', errors='coerce')
    
    #Busacamos la fila donde la fecha de la tarea o WO sea menor o igual a la fecha de retiro del personal
    mask_Fecha = (
        dfAssociate['Fecha Retiro de la Torre (DD/MM/AAAA)'].notna() &
        (row[columnDate] <= dfAssociate['Fecha Retiro de la Torre (DD/MM/AAAA)'])
    )
    
    if mask_Fecha.any():
        # Si hay coincidencias, devolvemos la torre asignada
        return dfAssociate.loc[mask_Fecha, 'Torre'].values[0]
    else:
        # Si no hay coincidencias, devolvemos la última fila
        return dfAssociate['Torre'].iloc[-1] if not dfAssociate['Torre'].empty else None
