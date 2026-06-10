import pandas as pd
import unicodedata
import re

import reports.func.getTorre as gT
import reports.func.readDocuments as gtDc
import reports.func.getDataApi as getApi 

#Definimos la función que permite eliminar tildes y caracteres especiales
def normalizarTexto(texto):
    if not isinstance(texto, str):
        return texto
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto.strip().lower()

#Se obtiene el insumo de CMDB
def getInsumoCMDB(initialDate, endDate, wo1, wo2, parametros):
    
    #Lectura de datos
    dfOriginalCRQ = getApi.getCRQs(initialDate, endDate)
    datos = gtDc.getData(parametros, "CMDB", False, wo1, wo2)
    dfOriginalWO = datos["datos_WOs"]
    dfGrupoOCHelix = datos["GrupoHelix"]
    dfAsociadosTCS = datos["AsociadosTCS"]
        
    dfCRQ = dfOriginalCRQ[['Codigo Orden', 'Categoria', 'Estado', 'Resumen', 'Codigo Tarea', 'Tarea', 'Resumen Tarea', 'Asignado', 'Grupo Asignado', 'Estado Tarea', 'Motivo Del Estado', 'Fecha Creacion CRQ', 'Hora Fin Tarea']]
    dfWO = dfOriginalWO[['NumeroCaso', 'Oferta', 'EstadoCaso', 'ResumenWO', 'Analistadecapacidadasignado', 'GrupoCapacidadAsignado', 'MotivoEstadodeWO', 'FechaCreacionWO', 'FechaCierre']]
    
    #Unimos los dataframe de CRQ y WO
    dfTrabajo = pd.DataFrame({
        'Codigo Orden': pd.concat([dfCRQ['Codigo Orden'], dfWO['NumeroCaso']], ignore_index=True),
        'Categoria': pd.concat([dfCRQ['Categoria'], dfWO['Oferta']], ignore_index=True),
        'Estado': pd.concat([dfCRQ['Estado'], dfWO['EstadoCaso']], ignore_index=True),
        'Resumen': pd.concat([dfCRQ['Resumen'], dfWO['ResumenWO']], ignore_index=True),
        'Codigo Tarea': pd.concat([dfCRQ['Codigo Tarea'], pd.Series([None]*len(dfWO))], ignore_index=True),
        'Tarea': pd.concat([dfCRQ['Tarea'], dfWO['ResumenWO']], ignore_index=True),
        'Resumen Tarea': pd.concat([dfCRQ['Resumen Tarea'], pd.Series([None]*len(dfWO))], ignore_index=True),
        'Asignado': pd.concat([dfCRQ['Asignado'], dfWO['Analistadecapacidadasignado']], ignore_index=True),
        'Grupo Asignado': pd.concat([dfCRQ['Grupo Asignado'], dfWO['GrupoCapacidadAsignado']], ignore_index=True),
        'Estado Tarea': pd.concat([dfCRQ['Estado Tarea'], dfWO['EstadoCaso']], ignore_index=True),
        'Motivo Del Estado': pd.concat([dfCRQ['Motivo Del Estado'], dfWO['MotivoEstadodeWO']], ignore_index=True),
        'Fecha Creacion': pd.concat([dfCRQ['Fecha Creacion CRQ'], dfWO['FechaCreacionWO']], ignore_index=True),
        'Hora Fin Tarea': pd.concat([dfCRQ['Hora Fin Tarea'], dfWO['FechaCierre']], ignore_index=True),
    })
    
    #Creamos la columa 'Torre Grupos' que trae la torre por grupo 
    dfTrabajo = gT.getTorreGrupo(dfTrabajo, dfGrupoOCHelix)
    
    #Cereamos la columna 'Torre Asignado' que trae la torre por el Asignado
    dfTrabajo = gT.getTorreAsociado(dfTrabajo,dfAsociadosTCS)
    
    #filtramos dataframe de CRQs por tarea que tiene cmdb
    dfTrabajo["Tarea"] = dfTrabajo["Tarea"].apply(
    lambda x: x if pd.notna(x) and re.search(r"cmdb|actualizar elementos de configuracion afectado" , normalizarTexto(str(x))) else None
    )
    
    #Eliminamos las filas que no tienen tarea de CMDB
    dfTrabajo = dfTrabajo.dropna(subset=['Tarea'])
    
    #Creamos la Torre Informe dando preferencias a la columna de Torre Asignado TCS
    dfTrabajo = gT.getTorreInforme(dfTrabajo)
    
    #Eliminamos las columnas que no son necesarias
    dfTrabajo = dfTrabajo.drop(columns=['Torre Asignado TCS', 'Torre Grupos']).rename(columns={'Torre Informe': 'Torre'})
    
    #Filtramos el dataframe por medio de la Torre para dejas solo a "Wintel", "storage" y las vacias
    dfTrabajo["Torre"] = dfTrabajo["Torre"].apply(
    lambda x: x if pd.notna(x) and re.search(r"wintel|storage", normalizarTexto(str(x))) else None
    )
    
    dfTrabajo = dfTrabajo.dropna(subset=["Torre"])
    
    return {"insumoCMDB": dfTrabajo, "Datos CRQ": dfOriginalCRQ, "Datos WO": dfOriginalWO}