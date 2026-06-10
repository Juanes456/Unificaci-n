import pandas as pd

def getData (Parametros, typeReports, calculateSLA=False, WO1=None, WO2=None):
    '''
        Esta función lee los archivos de excel respectivo y entrega los data frames respectivo con los duplicados eliminados por el numero de caso dependido del tipo de informe a realizar
        
        Parametros: la ruta donde se encuentra el archivo de parámetros (es un requisito para cualquier tipo de informe)
        WO1: ruta donde se encuentra el archivo de WOs correspondiente del 1 al 15 del mes
        WO2: ruta donde se encuentra el archivo de WOs correspondiente del 16 al 30 del mes
        typeReports: es un texto que indica el tipo de informe a realizar los únicos valores validos son ["WOs", "CMDB", "SLA"]
        calculateSLA (bool): indica si se desea calcular el SLA, por defecto es False
        
        return:
        dependio del tipo de reporte retorna un diccionario de todas las WOs como tambien los data frame correspondientes al archivo de parámetros.
        
    '''
    try:
        if not Parametros:
            raise ValueError("Es necesario la ruta del archivo de Parámetros")
        else:
            grupoHelix = pd.read_excel(Parametros, sheet_name = 'Grupos OC Helix', header= 0)
            asociadosTCS = pd.read_excel(Parametros, sheet_name = 'AsociadosTCS', header=0)
            if calculateSLA:
                dfCatalogo = pd.read_excel(Parametros, sheet_name = 'Catalogo (Helix)', header=0, keep_default_na=False)
                dftipoNovCat = pd.read_excel(Parametros, sheet_name = 'TipoNovedad-Categoria', header=0, keep_default_na=False)
                dftipoSol = pd.read_excel(Parametros, sheet_name = 'TipoSolicitud', header=0, keep_default_na=False)
                dftipoNov = pd.read_excel(Parametros, sheet_name = 'TipoNovedad', header=0)
            
            if typeReports in ['Incidentes abiertos', 'Incidentes cerrados']:
                dataResult = {'GrupoHelix': grupoHelix, 'AsociadosTCS': asociadosTCS}
            
            elif typeReports in ['WOs', 'CMDB']:
                if not WO1 or not WO2:
                    raise ValueError("Las rutas de los archivos de los datos de las WO debe ser especificado")
                
                dfWo1 = pd.read_excel(WO1, header=0)
                dfWo2 = pd.read_excel(WO2, header=0)
                datosWOs = pd.concat([dfWo1, dfWo2], ignore_index=True)
                dates = [
                    'fechaCreacionPedido',
                    'UltimaFechaModificacionPedido',
                    'FechaCreacionWO',
                    'FechaCierre',
                    'FechaProgramadaInicio',
                    'FechaProgramadaFin',
                    'fechaInicioTarea',
                    'fechaFinTarea'
                ]
                for col in dates:
                    if col in datosWOs.columns:
                        if not pd.api.types.is_datetime64_any_dtype(datosWOs[col]):
                            datosWOs[col] = datosWOs[col].astype(str)
                            datosWOs[col] = (
                                datosWOs[col]
                                .str.replace('a. m.', 'AM', regex=False)
                                .str.replace('p. m.', 'PM', regex=False)
                            )
                            datosWOs[col] = pd.to_datetime(
                                datosWOs[col],
                                format="%d/%m/%Y %I:%M:%S %p",
                                errors='coerce'
                            )
                if typeReports == 'CMDB':
                     dataResult = {'datos_WOs': datosWOs, 'GrupoHelix': grupoHelix, 'AsociadosTCS': asociadosTCS}
                else:
                    if calculateSLA:
                        dataResult = {'datos_WOs': datosWOs, 'GrupoHelix': grupoHelix, 'AsociadosTCS': asociadosTCS, 
                                      'CatalogoHelix': dfCatalogo, 'TipoNovedadCategoria': dftipoNovCat, 'TipoNovedad': dftipoNov, 'TipoSolicitud': dftipoSol}
                    else:
                        dataResult = {'datos_WOs': datosWOs, 'GrupoHelix': grupoHelix, 'AsociadosTCS': asociadosTCS}
            
            elif typeReports == 'CRQs':
                if calculateSLA:
                    dataResult = {
                        'GrupoHelix': grupoHelix,
                        'AsociadosTCS': asociadosTCS,
                        'CatalogoHelix': dfCatalogo,
                        'TipoNovedadCategoria': dftipoNovCat,
                        'TipoNovedad': dftipoNov,
                        'TipoSolicitud': dftipoSol
                    }
                else:
                    dataResult = {'GrupoHelix': grupoHelix, 'AsociadosTCS': asociadosTCS}    
            else:
                raise ValueError("El tipo de reporte no ha sido especificado")
            
            return dataResult
                
    except Exception as e:
        print(f"Error: {e}")
        return None
    
if __name__ == '__main__':
    path = 'C:\\Users\\2898604\\Downloads\\Pruebas WO\\'
    wo1 = path + 'WO y TASK Plataformas Centrales v2 1.xlsx'
    wo2 = path + 'WO y TASK Plataformas Centrales v2.xlsx'
    parameter = path + 'Parametros-CATALOGO Validaciones 3(Revision).xlsx'
    
    data = getData(parameter, 'WOs', True, wo1, wo2)['datos_WOs']

    data.to_csv(path + 'datosWOS.csv', index=False)