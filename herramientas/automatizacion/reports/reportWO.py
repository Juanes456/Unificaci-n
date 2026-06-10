import pandas as pd

import reports.func.staff as staff
import reports.func.getTorre as gT
import reports.func.change as ch
import reports.func.filters as filters
import reports.func.calculateSLA as sla
from reports.func.readDocuments import getData as gtDc

def getReportWO(wo1, wo2, parameters, calculateSLA):
    '''
        Esta función permite la consulta a los archivos de WOs y la manipulación de los datos de las WOs.
        Parameters:
            wo1 (str): Ruta del archivo de WOs correspondiente del 1 al 15 del mes
            wo2 (str): Ruta del archivo de WOs correspondiente del 16 al 30 del mes
            parameters (str): Ruta del archivo de parámetros
            calculateSLA (bool): Indica si se desea calcular el SLA
        Returns:
            dict: Un diccionario con los dataframes de las WOs
    '''
    
    #Lectura de datos
    data = gtDc(parameters, 'WOs', calculateSLA, wo1, wo2)
    dfOriginal = data['datos_WOs']
    dfGroupHelix = data['GrupoHelix']
    dfAsociados = data['AsociadosTCS']
    print(f'Lectura de WOs finalizada con {len(dfOriginal)} registros')
    #Creamos las columnas de trabajo en un nuevo dataframe
    dfWork = dfOriginal.copy()
    dfWork = dfWork.assign(**{
        'Eliminar': None,
        'Torre Asignado x Task': None,
        'Torre Grupos x Task': None,
        'Torre Asignado x WO': None,
        'Torre Grupos x WO': None,
        'Torre Informe': None
    })

    #Filtramos los datos de las WOs que tiene tareas
    dfWOTask = dfWork[pd.notna(dfWork['SecuenciaTarea'])].copy()
    
    #Traemos la torre del usuario asignado a la tarea
    dfWOTask['Torre Asignado x Task'] = dfWOTask.apply(
        lambda row: staff.staffFilterWO(row, dfAsociados, 'fechaFinTarea', 'UsuarioAsignado'),
        axis=1
    )
    dfWork.update(dfWOTask[['Torre Asignado x Task']])
    
    #Filtramos las tareas que no tiene usuario asignado
    dfWOTask = dfWOTask[pd.isna(dfWOTask['UsuarioAsignado'])].copy()
    
    #Traemos la torre del grupo asignado a la tarea
    dfWOTask['Torre Grupos x Task'] = dfWOTask.apply(
        lambda row: gT.getTorreGrupoWO(row['Grupoasignadotarea'], dfGroupHelix),
        axis=1
    )
    dfWork.update(dfWOTask[['Torre Grupos x Task']])
    
    #Ahora filtramos las WO que no tienen tareas
    dfOnlyWO = dfWork[pd.isna(dfWork['SecuenciaTarea'])].copy()
    
    #Traemos la torre del usuario asignado a la WO
    dfOnlyWO['Torre Asignado x WO'] = dfOnlyWO.apply(
        lambda row: staff.staffFilterWO(row, dfAsociados, 'FechaCierre', 'Analistadecapacidadasignado'),
        axis=1
    )
    dfWork.update(dfOnlyWO[['Torre Asignado x WO']])
    
    #Filtramos las WO que no tienen usuario asignado
    dfOnlyWO = dfOnlyWO[pd.isna(dfOnlyWO['Analistadecapacidadasignado'])].copy()
    
    #Traemos la torre del grupo asignado a la WO
    dfOnlyWO['Torre Grupos x WO'] = dfOnlyWO.apply(
        lambda row: gT.getTorreGrupoWO(row['GrupoCapacidadAsignado'], dfGroupHelix),
        axis=1
    )
    dfOnlyWO['Torre Grupos x WO'] = dfOnlyWO['Torre Grupos x WO'].replace('No TCS', None)
    dfWork.update(dfOnlyWO[['Torre Grupos x WO']])
    
    #Aplicamos los filtros a la columna Eliminar
    dfWork['Eliminar'] = dfWork.apply(filters.filtersWO, axis=1)
    
    #Unificamos las columnas en Torre Informe y eliminamos
    dfWork['Torre Informe'] = dfWork[['Torre Asignado x Task', 'Torre Grupos x Task', 'Torre Asignado x WO', 'Torre Grupos x WO']].bfill(axis=1).iloc[:, 0]
    dfWork['Torre Informe'] = dfWork['Torre Informe'].str.replace('Pract_', '')
    
    dfWork.drop(columns=['Torre Asignado x Task', 'Torre Grupos x Task', 'Torre Asignado x WO', 'Torre Grupos x WO'], inplace=True)
    
    if calculateSLA:
        #Tramemos los demas archivos de parametros
        dfCatalogo = data['CatalogoHelix']
        dfTipoSolicitud = data['TipoSolicitud']
        dfTipoNovedad = data['TipoNovedad']
        dfTNov_Cat = data['TipoNovedadCategoria']
        
        #Creamos las demás columnas de trabajo vacias
        dfWork = dfWork.assign(**{
            'Tipo de Cambio': None,
            'SLA_4.1': None,
            'SLA_4.2': None,
            'Detalle Categoria': None,
            'Cumplimiento SLA 4.1': None,
            'Cumplimiento SLA 4.2': None
        })
        
        #Trabajamos con los datos vacios de la columna eliminar
        dfWO_filtered = dfWork[pd.isna(dfWork['Eliminar'])].copy()
        
        #Determinamos los valores a partir del archivo de parámetros
        dfWO_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = dfWO_filtered.apply(
            lambda row: ch.typeChangeWO(row, dfCatalogo, dfTipoSolicitud),
            axis = 1,
            result_type = 'expand'
        )
        dfWork.update(dfWO_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']])
        
        #Determinamos a partir del tipo de solicitud
        dfWO_filtered = dfWork[
            (pd.notna(dfWork['TipoSolicitud'])) & (
            (dfWork['Tipo de Cambio'].str.contains('depende de la propiedad "tipo de solicitud"', case=False, na=False)) |
            (dfWork['Tipo de Cambio'] == '3. Torre y categoria encontrada pero no la tarea') |
            (dfWork['Tipo de Cambio'] == '2. Categoria no registrada para la torre') |
            (dfWork['Tipo de Cambio'] == '4. No se logra diferenciar la tarea')
        )].copy()
        
        if len(dfWO_filtered)>0:
            dfWO_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = dfWO_filtered.apply(
                lambda row: ch.typeSol(row, dfTipoSolicitud),
                axis = 1,
                result_type = 'expand'
            )
        
        dfWork.update(dfWO_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']])
        
        #Determinamos a partir del tipo de novedad
        dfWO_filtered = dfWork[
            (dfWork['Tipo de Cambio'].str.contains('depende de la propiedad "tipo de novedad"', case=False, na=False)) |
            (dfWork['Tipo de Cambio'] == '3. Torre y categoria encontrada pero no la tarea') |
            (dfWork['Tipo de Cambio'] == '4. No se logra diferenciar la tarea')
        ].copy()
        
        if len(dfWO_filtered)>0:
            dfWO_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = dfWO_filtered.apply(
                lambda row: ch.typeNov(row, dfTipoNovedad, dfTNov_Cat),
                axis = 1,
                result_type = 'expand'
            )
        dfWork.update(dfWO_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']])
        
        #Filtramos por las WO o tareas que no se pueden determinar el SLA para validar manualmente
        dfWO_filtered = dfWork[
            (dfWork['Tipo de Cambio'].str.contains('depende de la propiedad "tipo de solicitud"', case=False, na=False)) |
            (dfWork['Tipo de Cambio'].str.contains('depende de la propiedad "tipo de novedad"', case=False, na=False)) |
            (dfWork['Tipo de Cambio'] == '1. Categoria no encontrada') |
            (dfWork['Tipo de Cambio'] == '2. Categoria no registrada para la torre') |
            (dfWork['Tipo de Cambio'] == '3. Torre y categoria encontrada pero no la tarea') |
            (dfWork['Tipo de Cambio'] == '4. No se logra diferenciar la tarea')
        ].copy()
        
        if len(dfWO_filtered)>0:
            dfWO_filtered['Eliminar'] = '10. Validar manualmente'
            dfWork.update(dfWO_filtered[['Eliminar']])
            
        #Determinamos el cumplimiento del SLA
        dfWO_filtered = dfWork[(pd.isna(dfWork['Eliminar'])) | (dfWork['Eliminar'] == '')]
        dfWO_filtered = sla.SLACompliance(dfWO_filtered, isWO=True)
        dfWork.update(dfWO_filtered[['Cumplimiento SLA 4.1', 'Cumplimiento SLA 4.2']])
    
    return {'Datos WO': dfWork}


#Ejemplo de Uso
if __name__ == '__main__':
    path = 'C:\\Users\\2898604\\Downloads\\Pruebas WO\\'
    wo1 = path + 'WO y TASK Plataformas Centrales v2 1.xlsx'
    wo2 = path + 'WO y TASK Plataformas Centrales v2.xlsx'
    parameter = path + 'Parametros-CATALOGO Validaciones 3(Revision).xlsx'
    
    data = getReportWO(wo1, wo2, parameter, True)['Datos WO']
    data.to_csv(path + 'datosWOS.csv', index=False)
    print('terminado')