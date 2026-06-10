import pandas as pd
import numpy as np
import reports.func.getTorre as gT
from datetime import timedelta
from reports.func.getDataApi import getFinalizedIncident
from reports.func.readDocuments import getData as gtDc

def getReportFinishInc(initialDate, endDate, parameters):
    '''
        En esta función se realiza el tratamiento de la informacion de la api con el archivo de parámetros se exporta un diccionario con un dataframe para almacenar en una plantilla de excel.
        params:
            initialDate (str): fecha en formato YYYY-MM-DD que indica el inicio del reporte
            endDate (str): fecha en formato YYYY-MM-DD que indica el fin del reporte
            parameters (str): diccionario con los parámetros para la consulta
        return:
            dict: diccionario con el dataframe para la plantilla de excel
    '''
    #Modificamos la fecha final a un día demás para traer los datos que se encuentren hasta el final del día seleccionado y damos el formato de fecha
    endDate = (endDate + timedelta(days=1)).strftime('%Y-%m-%d')
    initialDate = initialDate.strftime('%Y-%m-%d')
    df = getFinalizedIncident(initialDate, endDate)
    
    try:
        if len(df) == 0:
            raise ValueError('No hay datos para analizar')
        #Leemos las hojas necesarias para el tratamiento de la info desde el archivo de parametros u obtenemos de Helix API/DB
        from reports.func.getHelixParameters import get_helix_parameters
        dfGroups, dfAssociate = get_helix_parameters(parameters, 'Incidentes cerrados')
        
        #Traemos la torre por asignado y por grupo asignado de los datos
        df = gT.getTorreAsociado(df, dfAssociate)
        df = gT.getTorreGrupo(df, dfGroups)
        df = gT.getTorreInforme(df)
        
        #Nos quedamos solo con la columna unificada y eliminamos los registros que no tengan torre
        df.drop(columns=['Torre Grupos', 'Torre Asignado TCS'], inplace=True)
        df['Torre Informe'] = df['Torre Informe'].str.strip().replace("No TCS", None)
        df = df.dropna(subset=["Torre Informe"])
        df = df[df['Torre Informe'].str.strip() != '']
        
        #Modificamos el nombre algunas columnas
        df.rename(columns={'Asignado': 'Usuario Asignado', 'Torre Informe': 'Torre'}, inplace=True)
        
        #Creamos una nueva columna para indicar si cumple SLA
        sla = {
            'Dentro del objetivo de servicio': 'A Tiempo',
            'Objetivo de servicio incumplido': 'Vencido'
        }
        
        df.insert(6, 'SLA', df['Cumplimiento ANS'].map(sla).fillna(''))
        df.insert(9, 'Cumple SLA', np.where(df['SLA'] == 'A Tiempo', 'TRUE', 'FALSE'))
        
        #Eliminamos la columna de cumplimiento ANS
        df.drop(columns=['Cumplimiento ANS'], inplace=True)
        df['Semana'] = None
        return {"Data": df}
    except ValueError as e:
        print(f'Error: {e}')
        return None
    