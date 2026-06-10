import pandas as pd
from reports.func.calculateSLA import SLACompliance as sla

def validateSLA(path: str):
    '''
        Esta funcion permite determinar el cumplimiento de los SLA para los casos en que se requirieron la validacion manual
        Parameters:
            path (str): Ruta del archivo de reporte
        Returns:
            pd.DataFrame: DataFrame con los resultados de la validación
    '''
    
    # Cargar el archivo de Excel
    date_columns = ['Fecha Creacion CRQ', 'Ultima Modificacion', 'Fecha Cierre CRQ', 'Fecha inicio programada', 'Fecha fin programada', 'Hora Inicio Tarea', 'Hora Fin Tarea', 'Hora Inicio Programada Tarea', 'Hora Fin Programada Tarea', 'Tiempo Asignado', 'Inicio Tarea Sistema', 'Cerro Tarea Sistema']
    dataCRQ = pd.read_excel(path, sheet_name='Datos CRQ', header=0, keep_default_na=False, parse_dates= date_columns)
    date_columns = ['fechaCreacionPedido', 'UltimaFechaModificacionPedido', 'FechaCreacionWO', 'FechaCierre','FechaProgramadaInicio', 'FechaProgramadaFin', 'fechaInicioTarea', 'fechaFinTarea']
    dataWO = pd.read_excel(path, sheet_name='Datos WO', header=0, keep_default_na=False, parse_dates=date_columns)

    if dataCRQ.empty and dataWO.empty:
        raise ValueError('No se pudo leer el archivo o no contiene datos válidos')
    
    #Filtramos por los campos que no tengan cumplimiento de SLA
    dataCRQ_filtered = dataCRQ[
        (
            (pd.isna(dataCRQ['Eliminar'])) |
            (dataCRQ['Eliminar'] == '')
        ) &
        (
            (pd.isna(dataCRQ['Cumplimiento SLA 4.1'])) | 
            (dataCRQ['Cumplimiento SLA 4.1'] == '') |
            (pd.isna(dataCRQ['Cumplimiento SLA 4.2'])) | 
            (dataCRQ['Cumplimiento SLA 4.2'] == '')
        )
    ].copy()
    dataWO_filtered = dataWO[
        (
            (pd.isna(dataWO['Eliminar'])) |
            (dataWO['Eliminar'] == '')
        ) &
        (
            (pd.isna(dataWO['Cumplimiento SLA 4.1'])) |
            (dataWO['Cumplimiento SLA 4.1'] == '') |
            (pd.isna(dataWO['Cumplimiento SLA 4.2'])) |
            (dataWO['Cumplimiento SLA 4.2'] == '')
        )
    ].copy()
    
    if len(dataCRQ_filtered) > 0:
        dataCRQ_filtered = sla(dataCRQ_filtered)
        dataCRQ.update(dataCRQ_filtered[['Cumplimiento SLA 4.1', 'Cumplimiento SLA 4.2']])
        
    if len(dataWO_filtered) > 0:
        dataWO_filtered = sla(dataWO_filtered, isWO=True)
        dataWO.update(dataWO_filtered[['Cumplimiento SLA 4.1', 'Cumplimiento SLA 4.2']])

    #Filtramos los datos de CRQ y WO que se necesitan para el reporte
    dataCRQ_filtered = dataCRQ[
        (pd.isna(dataCRQ['Eliminar'])) |
        (dataCRQ['Eliminar'] == '') |
        (dataCRQ['Eliminar'] == '10. Validar manualmente')
    ].copy()
    dataWO_filtered = dataWO[
        (pd.isna(dataWO['Eliminar'])) |
        (dataWO['Eliminar'] == '') |
        (dataWO['Eliminar'] == '10. Validar manualmente')
    ].copy()
    
    #Creamos el DataFrame de trabajo combinando los datos de CRQ y WO
    dfWork = pd.DataFrame({
        'OC': pd.concat([dataCRQ_filtered['Codigo Orden'], dataWO_filtered['NumeroCaso']], ignore_index=True),
        'Torre': pd.concat([dataCRQ_filtered['Torre Informe'], dataWO_filtered['Torre Informe']], ignore_index=True),
        'Tipo Cambio': pd.concat([dataCRQ_filtered['Tipo de Cambio'], dataWO_filtered['Tipo de Cambio']], ignore_index=True),
        'Codigo Tarea': pd.concat([dataCRQ_filtered['Codigo Tarea'], dataWO_filtered['IddeTarea']], ignore_index=True),
        'Tarea': pd.concat([dataCRQ_filtered['Tarea'], dataWO_filtered['ResumenWO']], ignore_index=True),
        'Grupo Asignado Tarea': pd.concat([dataCRQ_filtered['Grupo Asignado'], dataWO_filtered['GrupoCapacidadAsignado']], ignore_index=True),
        'Filial': pd.concat([dataCRQ_filtered['Filial'], dataWO_filtered['Compañia']], ignore_index=True),
        'Categoria': pd.concat([dataCRQ_filtered['Categoria'], dataWO_filtered['Oferta']], ignore_index=True),
        'Detalle Categoria': pd.concat([dataCRQ_filtered['Detalle Categoria'], dataWO_filtered['Detalle Categoria']], ignore_index=True),
        'SLA_4.1': pd.concat([dataCRQ_filtered['SLA_4.1'], dataWO_filtered['SLA_4.1']], ignore_index=True),
        'Cumplimiento SLA 4.1': pd.concat([dataCRQ_filtered['Cumplimiento SLA 4.1'], dataWO_filtered['Cumplimiento SLA 4.1']], ignore_index=True),
        'SLA_4.2': pd.concat([dataCRQ_filtered['SLA_4.2'], dataWO_filtered['SLA_4.2']], ignore_index=True),
        'Cumplimiento SLA 4.2': pd.concat([dataCRQ_filtered['Cumplimiento SLA 4.2'], dataWO_filtered['Cumplimiento SLA 4.2']], ignore_index=True),
        'Eliminar': pd.concat([dataCRQ_filtered['Eliminar'], dataWO_filtered['Eliminar']], ignore_index=True)
    })
    
    #Modificamos los datos y agragamos la columna de observaciones
    dfWork['Observaciones'] = None
    dfWork_filtered = dfWork[dfWork['Eliminar'] == '10. Validar manualmente'].copy()
    print(dfWork_filtered.head(3))
    cols = ['Tipo de Cambio', 'SLA_4.1', 'Cumplimiento SLA 4.1', 'SLA_4.2', 'Cumplimiento SLA 4.2', 'Detalle Categoria']
    if len(dfWork_filtered) > 0:
        dfWork_filtered['Observaciones'] = 'Por validar'
        dfWork_filtered[cols] = None
        dfWork.update(dfWork_filtered[cols + ['Observaciones']])
    #Eliminamos la columna 'Eliminar' ya que no es necesaria en el reporte final
    dfWork.drop(columns=['Eliminar'], inplace=True)
    return {
        'Reporte SLA': dfWork,
        'Datos CRQ': dataCRQ,
        'Datos WO': dataWO
    }  