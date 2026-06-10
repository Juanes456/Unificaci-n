import pandas as pd
import reports.func.getBusinessDate as gbd

def SLACompliance(df:pd.DataFrame, isWO:bool = False):
    '''
        Esta función calcula el cumplimiento del SLA 
        Parameters:
            df (pd.DataFrame): DataFrame de trabajo con todas las columnas necesarias
        Returns:
            pd.DataFrame: DataFrame actualizado con la columna 'Cumplimiento SLA'
    '''
    
    #Filtramos por los valores que no aplica SLA
    df_filtered = df[
        (pd.isna(df['SLA_4.1'])) |
        (df['SLA_4.1'] == 'N/A') |
        (df['SLA_4.1'] == 'NA') |
        (df['SLA_4.1'] == '')
        ].copy()
    
    if len(df_filtered)>0:
        df_filtered[['Cumplimiento SLA 4.1']] = 'N/A'
        df.update(df_filtered[['Cumplimiento SLA 4.1']])
        
    df_filtered = df[
        (pd.isna(df['SLA_4.2'])) |
        (df['SLA_4.2'] == 'N/A') |
        (df['SLA_4.2'] == 'NA') |
        (df['SLA_4.2'] == '')
        ].copy()
    
    if len(df_filtered)>0:
        df_filtered[['Cumplimiento SLA 4.2']] = 'N/A'
        df.update(df_filtered[['Cumplimiento SLA 4.2']])
        
    #Ahora filtramos por los valores que si aplica SLA 4.1
    df_filtered = df[
        (df['SLA_4.1'].str.strip().str.lower() != 'programada') &
        (df['SLA_4.1'].str.strip() != 'N/A') &
        (df['SLA_4.1'].str.strip() != 'NA') &
        (pd.notna(df['SLA_4.1']))
        ].copy()
    
    if len(df_filtered) > 0:
        df_filtered = sla(df_filtered, isWO=isWO)
        df.update(df_filtered[['Cumplimiento SLA 4.1']])
    
    #Ahora filtramos por los valores que si aplica SLA 4.2
    df_filtered = df[
        (df['SLA_4.2'].str.strip().str.lower() != 'programada') &
        (df['SLA_4.2'].str.strip() != 'N/A') &
        (df['SLA_4.2'].str.strip() != 'NA') &
        (pd.notna(df['SLA_4.2']))
        ].copy()

    if len(df_filtered) > 0:
        df_filtered = sla(df_filtered, isWO=isWO, is41=False)
        df.update(df_filtered[['Cumplimiento SLA 4.2']])
    
    #Determinamos los SLA para las programadas
    df_filtered = df[
        (df['SLA_4.1'].str.strip().str.lower() == 'programada')
        ].copy()
    
    if len(df_filtered) > 0:
        df_filtered['Cumplimiento SLA 4.1'] = df_filtered.apply(
            lambda x: slaProgramada(x, isWO=isWO), 
            axis=1
        )
        df.update(df_filtered[['Cumplimiento SLA 4.1']])
    return df

def sla(df: pd.DataFrame, isWO: bool = False, is41: bool = True):
    '''
        Esta función calcula el cumplimiento del SLA 4.1
        Parameters:
            df (pd.DataFrame): DataFrame de trabajo con todas las columnas necesarias
            isWo (bool): Indica si es WO o en el caso de CRQS
            is41 (bool): para determinar la columna si es 4.1 o 4.2
        Returns:
            pd.DataFrame: DataFrame actualizado con la columna 'Cumplimiento SLA 4.1'
    '''
    
    if is41:
        columnSLA = 'SLA_4.1'
        colCumpSLA = 'Cumplimiento SLA 4.1'
    else:
        columnSLA = 'SLA_4.2'
        colCumpSLA = 'Cumplimiento SLA 4.2'
    
    #En el caso de las WO vereficamos si tiene o no tareas
    if isWO:
        df_filtered = df[(pd.isna(df['SecuenciaTarea']))].copy()
        if len(df_filtered) > 0:
            df_filtered['fecha_limite'] = df_filtered.apply(
                lambda x: gbd.limitDate(x['FechaCreacionWO'], x[columnSLA], x['Compañia']) 
                if pd.notna(x['FechaCreacionWO']) else 'Sin fecha de creacion',
                axis=1
            )
            df_filtered[colCumpSLA] = df_filtered.apply(
                lambda x: 'Sin fecha de cierre' if pd.isna(x['FechaCierre']) else ('A Tiempo' if x['FechaCierre'] <= x['fecha_limite'] else 'Vencido'),
                axis=1
            )
            df.update(df_filtered[[colCumpSLA]])
            
        # Aplicamos lo mismo en caso de haber tareas
        df_filtered = df[(pd.notna(df['SecuenciaTarea']))].copy()
        if len(df_filtered) > 0:
            df_filtered['fecha_limite'] = df_filtered.apply(
                lambda x: gbd.limitDate(x['fechaInicioTarea'], x[columnSLA], x['Compañia'])
                if pd.notna(x['fechaInicioTarea']) else 'Sin fecha de creacion',
                axis=1
            )
            df_filtered[colCumpSLA] = df_filtered.apply(
                lambda x: 'Sin fecha de cierre' if pd.isna(x['fechaFinTarea']) else ('A Tiempo' if x['fechaFinTarea'] <= x['fecha_limite'] else 'Vencido'),
                axis=1
            )
            df.update(df_filtered[[colCumpSLA]])
    
    #En el caso de la CRQs nos fijamos en las tareas
    else:
        #Filtramos por los que no estan vacios de las fechas para el cálculo
        df_filtered = df[
            (pd.notna(df['Inicio Tarea Sistema'])) & 
            (pd.notna(df['Cerro Tarea Sistema']))
            ].copy()

        if len(df_filtered)>0:
            df_filtered['fecha_limite'] = df_filtered.apply(
                lambda x: gbd.limitDate(x['Inicio Tarea Sistema'], x['SLA_4.1'], x['Filial']),
                axis=1
            )
            df_filtered[colCumpSLA] = df_filtered.apply(
                lambda x: 'Sin fecha de cierre' if pd.isna(x['Cerro Tarea Sistema']) else ('No se pudo determinar la fecha límite' if pd.isna(x['fecha_limite']) else ('A Tiempo' if x['Cerro Tarea Sistema'] <= x['fecha_limite'] else 'Vencido')),
                axis=1
            )
            df.update(df_filtered[[colCumpSLA]])
            
        df_filtered = df[(pd.isna(df['Inicio Tarea Sistema']))].copy()
        if len(df_filtered)>0:
            df_filtered[colCumpSLA] = df_filtered.apply(
                lambda x: 'Sin fecha de inicio',
                axis=1
            )
            df.update(df_filtered[[colCumpSLA]])
            
        df_filtered = df[(pd.isna(df['Cerro Tarea Sistema']))].copy()
        if len(df_filtered)>0:
            df_filtered[colCumpSLA] = df_filtered.apply(
                lambda x: 'Sin fecha de cierre',
                axis=1
            )
            df.update(df_filtered[[colCumpSLA]])

    return df

def slaProgramada(row, isWO: bool = False):
    '''
        Esta función calcula el cumplimiento del SLA para las programadas
        Parameters:
            df (pd.DataFrame): DataFrame de trabajo con todas las columnas necesarias
            isWO (bool): Indica si es WO o en el caso de CRQS
        Returns:
            pd.DataFrame: DataFrame actualizado con la columna 'Cumplimiento SLA 4.1'
    '''
    if isWO:
        if pd.isna(row['SecuenciaTarea']):
            horaFinTarea = row['FechaCierre']
        return 'Programada'
    else:
        horaFinTarea = row['Hora Fin Tarea']
        horaFinProgramadaTarea = row['Hora Fin Programada Tarea']
        horaFinProgramadaCRQ = row['Fecha fin programada']
        
        if pd.notna(horaFinTarea):
            if pd.notna(horaFinProgramadaTarea):
                if horaFinTarea <= horaFinProgramadaTarea:
                    return 'A Tiempo'
                else:
                    return 'Vencido'
            else:
                if pd.notna(horaFinProgramadaCRQ):
                    if horaFinTarea <= horaFinProgramadaCRQ:
                        return 'A Tiempo'
                    else:
                        return 'Vencido'
                else:
                    return 'Sin fecha de comparación'
        else:
            return 'Sin fecha de cierre'