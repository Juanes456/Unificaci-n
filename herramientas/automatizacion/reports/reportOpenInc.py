import pandas as pd
import reports.func.getTorre as gT
from datetime import timedelta
from reports.func.getDataApi import getActiveIncident
from reports.func.readDocuments import getData as gtDc

def getReportOpenInc(initialDate, endDate, parameters):
    '''
        En esta función se realiza el tratamiento de la informacion de la api con el archivo de parámetros se exporta un diccionario con los diferentes dataframes
        
        params:
            initialDate (str): fecha en formato YYYY-MM-DD que indica el inicio del reporte
            endDate (str): fecha en formato YYYY-MM-DD que indica el final del reporte
            parameters (str): ruta donde se encuentra el archivo de parametros
            
        return
            dicc (dictionary): diccionario de dataframes
    '''
    #Modificamos el dia final a un día demás para traer los datos que se encuentren hasta el final del día seleccionado y damos el formato de fecha
    endDate = (endDate + timedelta(days=1)).strftime('%Y-%m-%d')
    initialDate = initialDate.strftime('%Y-%m-%d')
    
    #Obtemos el dataframe de inicidentes abiertos
    dfOpenInc = getActiveIncident(initialDate,endDate)
    
    try:
        if len(dfOpenInc)==0:
            raise ValueError('No hay datos para analizar')
    
        #Leemos las hojas necesarias para el tratamiento de la info desde el archivo de parametros u obtenemos de Helix API/DB
        from reports.func.getHelixParameters import get_helix_parameters
        dfGroups, dfAssociate = get_helix_parameters(parameters, 'Incidentes abiertos')
        
        #Traemos la torre por asignado y por grupo asignado de los datos
        dfWork = gT.getTorreAsociado(dfOpenInc,dfAssociate)
        dfWork = gT.getTorreGrupo(dfWork,dfGroups)
        
        #En caso de que el ticket notenga usuario asignado establecemos "SIN USUARIO ASIGNADO" para no dejar vacios
        dfWork['Asignado'] = dfWork.apply(
            lambda row: row['Asignado'] if pd.notna(row['Asignado']) else 'SIN USUARIO ASIGNADO',
            axis=1
        )
        
        #Modificamos el nombre algunas columnas
        dfWork.rename(columns={'Asignado':'Usuario Asignado'}, inplace=True)
                
        #En caso de no tener usuario asignado o integracion ignio se deja el grupo, de lo contrario dejamos la torre por grupos vacia
        dfWork['Torre Grupos'] = dfWork.apply(
            lambda row: row['Torre Grupos'] if row['Usuario Asignado'] in ['SIN USUARIO ASIGNADO','INTEGRACION IGNIO'] else '',
            axis=1
        )
        
        #unificamos las dos columnas de las torres dando prioridad a las que estan por usuario asignado
        dfWork = gT.getTorreInforme(dfWork)
        
        #Nos quedamos solo con la columna unificada, modificamos el nombre de la columna y eliminamos los registros que no tengan torre
        dfWork.drop(columns=['Torre Grupos', 'Torre Asignado TCS'], inplace=True)
        dfWork['Torre Informe'] = dfWork['Torre Informe'].str.strip().str.lower().replace("no tcs", None)
        dfWork = dfWork.dropna(subset=["Torre Informe"])
        dfWork = dfWork[dfWork['Torre Informe'].str.strip() != '']
        dfWork.rename(columns={'Torre Informe': 'Torre'}, inplace=True)
        
        #Creamos una nueva columna para indicar si cumple SLA
        dfWork.insert(6, 'SLA', None)
        dfWork['SLA']= dfWork.apply(
        lambda row: 'A Tiempo' if row['Cumplimiento ANS'] in ['Dentro del objetivo de servicio', 'Advertencia del objetivo de servicio', None, ''] else 'Vencido' if row['Cumplimiento ANS'] == 'Objetivo de servicio incumplido' else '',
        axis=1
        )
        
        #Separamos los datos en eventos e incidentes
        dfEvent = dfWork[dfWork['Tipo de Caso'] == 'Evento'][['SLA', 'Torre', 'Grupo Asignado']]
        dfIncident = dfWork[dfWork['Tipo de Caso'] == 'Incidente'][['SLA', 'Torre', 'Grupo Asignado']]
        
        #Obtenemos los grupos de eventos o incidentes que tiene SLA Vencido
        dfGroupExpiredEvent = dfEvent[dfEvent['SLA']=='Vencido'][['Grupo Asignado']]
        dfGroupExpiredIncident = dfIncident[dfIncident['SLA']=='Vencido'][['Grupo Asignado']]
        
        #Eliminamos las columnas 'Grupo Asignado' para luego hacer pivot
        dfEvent.drop(columns=['Grupo Asignado'], inplace=True)
        dfIncident.drop(columns=['Grupo Asignado'], inplace=True)
        
        #Realizamos pivot en el dataframe para obtener un resumen
        dfEvent = pivotTable(dfEvent)
        dfIncident = pivotTable(dfIncident)
        
        #Conatabilizamos la cantidad de vencidos que se encuentran por grupo asignado
        dfGroupExpiredEvent['Total Vencidos'] = dfGroupExpiredEvent.groupby('Grupo Asignado')['Grupo Asignado'].transform('count')
        dfGroupExpiredIncident['Total Vencidos'] = dfGroupExpiredIncident.groupby('Grupo Asignado')['Grupo Asignado'].transform('count')
        dfGroupExpiredEvent.drop_duplicates(subset=['Grupo Asignado']).reset_index(drop=True)
        dfGroupExpiredIncident.drop_duplicates(subset=['Grupo Asignado']).reset_index(drop=True)
        
        return {
            'Reporte': dfWork,
            'Datos': dfOpenInc,
            'Eventos': {
                'Resumen SLA por Torre': dfEvent,
                'Grupos con eventos vencidos': dfGroupExpiredEvent
            },
            'Incidentes':{
                'Resumen SLA por Torre': dfIncident,
                'Grupos con incidentes vencidos': dfGroupExpiredIncident
            }
        }
    except ValueError as ve:
        print(f'Error: {ve}')
        return None

def pivotTable(df):
    '''
        Genera tablas resumen para incidentes/eventos abiertos por torre, si no hay datos, se devuelve una tabla con columna "Sin Datos" y fila "Total" en 0.
        
        Params:
            df (DataFrame): Datos originales con columnas 'SLA' y 'Torre' 
            
        Returns:
            tabla (DataFrame): Tabla resumen de SLA por Torre

    '''
    if df.empty:
        tabla = pd.DataFrame({'Sin Datos': [0]}, index=['Total'])
    else:
        tabla = pd.crosstab(df['SLA'], df['Torre'])
        tabla['Sub total'] = tabla.sum(axis=1)
        tabla.loc['Total'] = tabla.sum()
    
    tabla = tabla.reset_index()
    tabla.rename(columns={'index':''}, inplace=True, errors='ignore')
    return tabla