import pandas as pd

import reports.func.filters as ft
import reports.func.change as chg
import reports.func.staff as stf
import reports.func.getTorre as gT
import reports.func.getDataApi as getApi

from datetime import timedelta
from reports.func.readDocuments import getData as gtDc
from reports.func.calculateSLA import SLACompliance as sla

#Se crea la funcion que genera el reporte de CRQ
def getReportCRQ(initialDate, endDate, parametros, calculateSLA):
    
    '''
        Esta función permite la consulta a la API y la manipulación de los datos de las CRQs tanto de bancolombia como de banistmo.
        
        Parameters:
            intialDate (str): Fecha de incio del reporte seleccionado por el usuario
    '''
    
    #Lectura de datos
    endDate = (endDate + timedelta(days=1)).strftime('%Y-%m-%d')
    initialDate = initialDate.strftime('%Y-%m-%d')
    dataCRQs = getApi.getCRQs(initialDate, endDate)
    dfGroupHelix = gtDc(parametros, 'CRQs')['GrupoHelix']
    dfAsociados = gtDc(parametros, 'CRQs')['AsociadosTCS']
    
    #Determinamos la torre de los asocioados asignados teniendo en cuenta los casos en que la fecha de retiro es importante
    dfWork = stf.staffFilter(dataCRQs, dfAsociados, initialDate)
    
    #Traemos la torre respecto al grupo asignado
    dfWork = gT.getTorreGrupo(dfWork, dfGroupHelix)
    
    #Reemplazamos los datos que son No TCS de la columan de Torre Grupos por vacios
    dfWork['Torre Grupos'] = dfWork['Torre Grupos'].str.strip().str.lower().replace("no tcs", None)
    
    #Se crea la columna Torre Informe que se llena, preferiblemente con los datos de la columna Torre Asignado TCS en caso de que no este vacia de lo contrario se llena con los valores de Torre Grupo
    dfWork = gT.getTorreInforme(dfWork)
    dfWork['Torre Informe'] = dfWork['Torre Informe'].str.replace('Pract_', '')
    
    #Se crea la columna Eliminar en la columna 34 y se aplican filtros
    dfWork.insert(34,'Eliminar',None)
    dfWork['Eliminar'] = dfWork.apply(ft.filters, axis=1)
    
    #Eliminamos la columna Torre Asignado TCS y Torre Grupos
    dfWork.drop(columns=['Torre Asignado TCS', 'Torre Grupos'], inplace=True)
    
    if calculateSLA:
        dfCatalogo = gtDc(parametros, 'CRQs', calculateSLA)['CatalogoHelix']
        dftipoNovCat = gtDc(parametros, 'CRQs', calculateSLA)['TipoNovedadCategoria']
        dftipoNov = gtDc(parametros, 'CRQs', calculateSLA)['TipoNovedad']
        
        #Filtramos solo las filas vacias de la columna eliminar y traemos las 4 columnas de parametros 
        dfWork[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = None
        dataCRQ_filtered = dfWork[dfWork['Eliminar'].isna()].copy()
        
        dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = dataCRQ_filtered.apply(
            lambda row: chg.typeChange(row, dfCatalogo), axis=1, result_type='expand'
        )
        dfWork.update(dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']])
        
        dataCRQ_filtered = dfWork[
            (dfWork['Tipo de Cambio'] == '3. Torre y categoria encontrada pero no la tarea') |
            (dfWork['Tipo de Cambio'] == '4. No se logra diferenciar la tarea')
        ].copy()
        if len(dataCRQ_filtered)>0:
            dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = dataCRQ_filtered.apply(
            lambda row: chg.typeChange(row, dfCatalogo, 'word'), axis=1, result_type='expand'
            )
            
            dfWork.update(dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']])
            
        dataCRQ_filtered = dfWork[
            (dfWork['Tipo de Cambio'] == '3. Torre y categoria encontrada pero no la tarea') |
            (dfWork['Tipo de Cambio'] == '4. No se logra diferenciar la tarea')
        ].copy()

        if len(dataCRQ_filtered)>0:
            dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = dataCRQ_filtered.apply(
                lambda row: chg.typeChange(row, dfCatalogo, 'spacy'), axis=1, result_type='expand'
            )
            dfWork.update(dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']])
        
        #Finalmente filtramos los datos que no se han podido categorizar
        dataCRQ_filtered = dfWork[
            (dfWork['Tipo de Cambio'] == '1. Categoria no encontrada') |
            (dfWork['Tipo de Cambio'] == '2. Categoria no registrada para la torre') |
            (dfWork['Tipo de Cambio'] == '3. Torre y categoria encontrada pero no la tarea') |
            (dfWork['Tipo de Cambio'] == '4. No se logra diferenciar la tarea')
        ].copy()
        
        if len(dataCRQ_filtered)>0:
            dataCRQ_filtered['Eliminar'] = '10. Validar manualmente'
            dfWork.update(dataCRQ_filtered[['Eliminar']])
            
        #Filtramos los datos de tipo de cambio que dependen del tipo de novedad
        dataCRQ_filtered = dfWork[
            (pd.isna(dfWork['Eliminar'])) &
            (dfWork['Tipo de Cambio'] == 'Depende de la Propiedad "Tipo de Novedad"')
        ].copy()
        
        if len(dataCRQ_filtered)>0:
            dfCatHel_filtered = dfCatalogo[['Categoria', 'Categoria OC']]
            dfCatHel_filtered.drop_duplicates(subset=['Categoria'])
            
            #Encontramos los valores que dependen del tipo de novedad
            dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']] = dataCRQ_filtered.apply(
                lambda row: chg.typeNews(
                    row,
                    dfCatHel_filtered.loc[dfCatHel_filtered['Categoria'] == row['Categoria'], 'Categoria OC'].iloc[0],
                    dftipoNov,
                    dftipoNovCat
                ),
                axis=1,
                result_type='expand'
            )
            dfWork.update(dataCRQ_filtered[['Tipo de Cambio', 'SLA_4.1', 'SLA_4.2', 'Detalle Categoria']])
            
        #Filtramos los datos de tipo de cambio que aún tienen depencencias
        dataCRQ_filtered = dfWork[
            (pd.isna(dfWork['Eliminar'])) &
            (dfWork['Tipo de Cambio'] == 'Depende de la Propiedad "Tipo de Novedad"') |
            (dfWork['Tipo de Cambio'] == 'Depende de la Propiedad "Tipo de Solicitud"') |
            (dfWork['Tipo de Cambio'] == 'Depende de la Propiedad "Tipo de solicitud"')
        ].copy()
        if len(dataCRQ_filtered)>0:
            dataCRQ_filtered['Eliminar'] = '10. Validar manualmente'
            dfWork.update(dataCRQ_filtered[['Eliminar']])
            
        #Creamos las columnas de cumplimiento del SLA y determinamos el si cumple o no
        dfWork = dfWork.assign(**{
            'Cumplimiento SLA 4.1': None,
            'Cumplimiento SLA 4.2': None
        })
        
        dataCRQ_filtered = dfWork[(pd.isna(dfWork['Eliminar'])) | (dfWork['Eliminar'] == '')]
        dataCRQ_filtered = sla(dataCRQ_filtered)
        dfWork.update(dataCRQ_filtered[['Cumplimiento SLA 4.1', 'Cumplimiento SLA 4.2']])
        
    return {
        'Datos CRQ': dfWork
    }

#Ejemplo de uso   
if __name__ == '__main__':
    from datetime import datetime
    initialDate = datetime.strptime('2025-07-01', '%Y-%m-%d')
    endDate = datetime.strptime('2025-07-10', '%Y-%m-%d')
    path = 'C:\\Users\\2898604\\Downloads\\Pruebas WO\\'
    parameter = path + 'Parametros-CATALOGO Validaciones 3(Revision).xlsx'
 
    data = getReportCRQ(initialDate, endDate, parameter, True)['Datos CRQ']
    data.to_csv(path + 'datosCRQ.csv', index=False)
    print('terminado')
 