import pandas as pd
import unicodedata
import re
import reports.func.spacyChange as spcy

#Definimos la función que permite eliminar tildes y caracteres especiales
def normalizarTexto(texto):
    if not isinstance(texto, str):
        return texto
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = ' '.join(texto.split())
    texto = texto.strip().lower()
    texto = re.sub(r'\s+', ' ', texto)
    return texto

#Definimos dos funciónes que permite filtra por tareas, en la primera se implementa una similitud del 100% de coincidencia y la segunda se toma las que rechaza el primer filtro y valida ciertos casos especificos.
def matchTask_default(taskCatHel, taskRow):
    #Limipieza de datos
    for delimiter in ['_ ', ' _', ' _ ', '__', '\\n','\n', '\n_', '\n_ ', '\t', '\t ', ' \t', '\t_', '\t_ ', '    ']:
        taskCatHel = taskCatHel.replace(delimiter, '_')
        
    taskCatHel = re.sub(r' {3,}', '_', taskCatHel)
    #Separamos el texto en una lista de elementos
    tasksCatalogo = [normalizarTexto(t) for t in re.split(r'[_]+',taskCatHel) if t.strip()]
    taskRow = normalizarTexto(taskRow)
    
    return taskRow in tasksCatalogo
    
def matchTask_words(taskCatHel, taskRow):
    #Definimos verbos clave:
    verbs = {'ejecutar', 'validar', 'actualizar', 'implementar', 'bajar', 'subir', 'salvar', 'reprocesar', 'restaurar', 'retener'}
    #Limipieza de datos
    for delimiter in ['_ ', ' _', ' _ ', '__', '\\n','\n', '\n_', '\n_ ', '\t', '\t ', ' \t', '\t_', '\t_ ', '    ']:
        taskCatHel = taskCatHel.replace(delimiter, '_')
    
    taskCatHel = re.sub(r' {3,}', '_', taskCatHel)
    #Separamos el texto en una lista de elementos
    tasksCatalogo = [normalizarTexto(t) for t in re.split(r'[_]+',taskCatHel) if t.strip()]
    taskRow = normalizarTexto(taskRow)
    
    for task in tasksCatalogo:
        if task in taskRow:
            return True
        if taskRow in ['procesos malla', 'proceso malla'] and 'procesos malla' in task:
            return True
        if task == 'bajar y subir servicios':
            if any(word in taskRow for word in ['bajar', 'subir']):
                return True 
        taskWords = set(task.split())
        taskRowWords = set(taskRow.split())
        if len(taskRowWords & taskWords) >= 2:
            if any(v in taskWords and v in taskRowWords for v in verbs):
                return True
    return False

def typeChange(row, dfCatHel, matchTaskType = ''):
    """
    Esta función se encarga de traer el tipo de cambio y el detalle de la categoría
    basado en la información de la fila actual y los parámetros de configuración.
    
    Parameters:
    row (pd.Series): La fila actual del DataFrame.
    dfCatHel(pd.DataFrame): DataFrame con los parámetros de Catalogo Helix.

    Returns:
    tuple: Tipo de cambio y detalle de la categoría.
    """ 
    #Normalizamos los textos para evitar conflictos de tildes y mayusculas
    torreRow = normalizarTexto(row['Torre Informe'])
    
    #Filtramos el df del catalogo helix que coincida con la categoria del informe
    dfCatHel_filtered = dfCatHel[(dfCatHel['Categoria'].apply(lambda x: x == row['Categoria']))]
    
    #Verificamos que el filtro aplicado trae un valor y filtramos por torre
    if len(dfCatHel_filtered)>0:
        dfCatHel_filtered = dfCatHel_filtered[(
            dfCatHel_filtered['Torre'].apply(lambda x: torreRow in normalizarTexto(x))
            )]
        #Validamos la cantidad de valores encontrados por el filtro
        if len(dfCatHel_filtered) == 1:
            rowCatHel = dfCatHel_filtered.iloc[0]
            return (
                    rowCatHel['Tipo de Cambio'],
                    rowCatHel['SLA (A partir de Marzo 2021)'],
                    rowCatHel['Medición KPI (anexo 4.2)'],
                    rowCatHel['Detalle Categoría']
                )
        
        #Si encuentra más de un valor aplicamos filtro por tarea
        elif len(dfCatHel_filtered) > 1:
            match matchTaskType:
                case 'word':
                    dfCatHel_filtered = dfCatHel_filtered[
                        dfCatHel_filtered['Tareas'].apply(lambda x: matchTask_words(x, row['Tarea']))
                    ]
                case 'spacy':
                    dfCatHel_filtered = dfCatHel[(dfCatHel['Categoria'].apply(lambda x: x == row['Categoria']))]
                    dfCatHel_filtered = dfCatHel_filtered[(
                        dfCatHel_filtered['Torre'].apply(lambda x: torreRow in normalizarTexto(x))
                    )]
                    dfCatHel_filtered = spcy.matchTasks_spacy(dfCatHel_filtered, row['Tarea'])
                case _:
                    dfCatHel_filtered = dfCatHel_filtered[
                        dfCatHel_filtered['Tareas'].apply(lambda x: matchTask_default(x, row['Tarea']))
                    ]
                
            if len(dfCatHel_filtered) == 1:
                rowCatHel = dfCatHel_filtered.iloc[0]
                return (
                        rowCatHel['Tipo de Cambio'],
                        rowCatHel['SLA (A partir de Marzo 2021)'],
                        rowCatHel['Medición KPI (anexo 4.2)'],
                        rowCatHel['Detalle Categoría']
                    )
            elif len(dfCatHel_filtered)>1:
                return ('4. No se logra diferenciar la tarea',*[None]*3)
            
            else:
                return ('3. Torre y categoria encontrada pero no la tarea',*[None]*3)
        
        else:
            return ('2. Categoria no registrada para la torre',*[None]*3)
    
    else:
        return ('1. Categoria no encontrada',*[None]*3)

def typeNews(row, category, dfT_Nov, dfT_Nov_Cat):
    
    #De la tabla TipoNovedad-Categoria se selecciona los datos que corresponden a la categoria
    dfT_Nov_Cat = dfT_Nov_Cat[dfT_Nov_Cat['Categoria OC'] == category]
    dfT_Nov['Tipo Novedad - Normalizado'] = dfT_Nov['Tipo Novedad'].apply(normalizarTexto)
    #Busacamos la novedad en los datos en la decripción despues del texto "2. Cambio"
    novData = re.search(r"2\. Cambio:\s*[\r\n\-]*\s*([A-Za-z]+)", normalizarTexto(row['Descripcion']), re.IGNORECASE)
    typeCh, SLA_41, SLA_42, detail = row['Tipo de Cambio'], row['SLA_4.1'], row['SLA_4.2'], row['Detalle Categoria']
    if novData:
        novData = novData.group(1).strip()
        dfT_Nov_filtered = dfT_Nov['Tipo Novedad - Normalizado'].str.contains(novData, case=False, na=False)
        typeNov = dfT_Nov.loc[dfT_Nov_filtered, 'Tipo Cambio']
        if not typeNov.empty and len(typeNov) == 1:
            typeCh = typeNov.iloc[0]
            if typeCh == 'Aprovisionamiento':
                detail = dfT_Nov['Aprovisionamiento de Recursos Nuevos (Compra de un Servidor Físico, Almacenamiento)'].str.contains(novData, case=False, na=False)
                if not detail.empty and len(detail) == 1:
                    detail = 'Aprovisionamiento de Recursos Nuevos (Compra de un Servidor Físico, Almacenamiento)'
                else:
                    detail = 'Aprovisionamiento de Recursos Existentes (Servidores, Cores, Memoria, Disco)'
                    
            elif typeCh == 'Desaprovisionamiento':
                detail = 'Ocs de Eliminación/Disminución Recursos'
             
            dfT_Nov_Cat = dfT_Nov_Cat[dfT_Nov_Cat['Tipo Cambio'] == typeCh]
            if len(dfT_Nov_Cat) == 1:
                SLA_42 = dfT_Nov_Cat['Medición KPI (anexo 4.2)'].iloc[0]
                SLA_41 = dfT_Nov_Cat['SLA (A partir de Marzo 2021)'].iloc[0]
    
    return typeCh, SLA_41, SLA_42, detail

def typeChangeWO(row, dfCatHel:pd.DataFrame, dfTSol:pd.DataFrame):
    '''
       Función que permite determinar el tipo de cambio, SLA 4.1, SLA 4.2 y el detalle de la categoría a partir del archivo de parámetros de las WO,
       
        parametres:
            row (row-DataFrame) : Fila de trabajo de los datos de las WO
            dfCatHel (DataFrame): Catologo Helix del archivo de parametros
        
        return:
            tupla que contiene información relacionada con el tipo de cambio, SLA 4.1, SLA 4.2, detalle categoria 
    '''
    
    dfCatHel = dfCatHel[dfCatHel['Categoria'] == row['Oferta']]
    dfCatHel.drop_duplicates(subset=['Tareas'])
    if len(dfCatHel)>0:
        #Si en cuentra registros, filtramos por torre
        dfCatHel = dfCatHel[dfCatHel['Torre'] == row['Torre Informe']]
        if len(dfCatHel) > 0:
            if len(dfCatHel) == 1:
                rowCatHel = dfCatHel.iloc[0]
                return (
                    rowCatHel['Tipo de Cambio'],
                    rowCatHel['SLA (A partir de Marzo 2021)'],
                    rowCatHel['Medición KPI (anexo 4.2)'],
                    rowCatHel['Detalle Categoría']
                )
            else:
                if pd.notna(row['SecuenciaTarea']):
                    dfCatHel = dfCatHel[dfCatHel['Tareas'].apply(
                        lambda x: matchTask_default(x, row['NombreTarea'])
                    )]
                    if len(dfCatHel)>0:
                        if len(dfCatHel) == 1:
                            rowCatHel = dfCatHel.iloc[0]
                            return (
                                rowCatHel['Tipo de Cambio'],
                                rowCatHel['SLA (A partir de Marzo 2021)'],
                                rowCatHel['Medición KPI (anexo 4.2)'],
                                rowCatHel['Detalle Categoría']
                            )
                        return('4. No se logra diferenciar la tarea', *[None]*3)
                else:
                    dfTSol = dfTSol[dfTSol['Tipo Solicitud'].apply(
                        lambda x: matchTask_words(x, row['ResumenWO'])
                    )]
                    if len(dfTSol) == 1:
                        rowTSol = dfTSol.iloc[0]
                        tc, sla = rowTSol['Tipo Cambio'], rowTSol['SLA']
                        if tc == 'Estándar':
                            detail = 'OCs Estándar Ambientes Productivos'
                        else:
                            detail = 'Ocs de gestión'
                        return(
                            tc,
                            sla,
                            'N/A',
                            detail
                        )
                    else:
                        dfCatHel = dfCatHel[dfCatHel['Tareas'].apply(
                            lambda x: matchTask_words(x, row['ResumenWO'])
                        )]
                        if len(dfCatHel) == 1:
                            rowCatHel = dfCatHel.iloc[0]
                            return(
                                rowCatHel['Tipo de Cambio'],
                                rowCatHel['SLA (A partir de Marzo 2021)'],
                                rowCatHel['Medición KPI (anexo 4.2)'],
                                rowCatHel['Detalle Categoría']
                            )
                        else:
                            dfCatHel = dfCatHel[dfCatHel['Tareas'].apply(
                                lambda x: spcy.lemmaSimWO(x, row['ResumenWO'])
                            )]
                            if len(dfCatHel) == 1:
                                rowCatHel = dfCatHel.iloc[0]
                                return(
                                    rowCatHel['Tipo de Cambio'],
                                    rowCatHel['SLA (A partir de Marzo 2021)'],
                                    rowCatHel['Medición KPI (anexo 4.2)'],
                                    rowCatHel['Detalle Categoría']
                                )
                return ('3. Torre y categoria encontrada pero no la tarea', *[None]*3)  
        else:
            return ('2. Categoria no registrada para la torre', *[None]*3)          
    else:
        return ('1. Categoria no encontrada', *[None]*3)

def typeSol(row, dfTypeSol: pd.DataFrame):
    '''
        Funcion que permite determinar el SLA para las WO que dependen del tipo de solicitud
        parameters:
            row: fila del dato a determinar
            dfTypeSol : dataframe que contiene los datos de tipo se solicitud
            
        return:
            tupla: resultado de la busqueda
    '''
    
    #Determinamos el tipo de solicitud de los datos
    dfTypeSol = dfTypeSol[
        dfTypeSol['Tipo Solicitud'].str.contains(str(row['TipoSolicitud']), case=False, na=False, regex=False)
    ]
    
    tipoCamb, SLA1, SLA2, detalle = row['Tipo de Cambio'], row['SLA_4.1'], row['SLA_4.2'], row['Detalle Categoria']
    
    if len(dfTypeSol) == 1:
        tipoCamb = dfTypeSol['Tipo Cambio'].iloc[0]
        SLA1 = dfTypeSol['SLA'].iloc[0]
        SLA2 = 'N/A'
        if tipoCamb == 'Estándar':
            detalle = 'OCs Estándar Ambientes Productivos'
            dfTypeSol = dfTypeSol[
                dfTypeSol['Acuerdo Operativo'].str.contains(str(row['TipoSolicitud']), case=False, na=False, regex=False)
            ]
            if not len(dfTypeSol) == 0:
                SLA1 = dfTypeSol['Medición Acuerdo operativo'].iloc[0]
        elif tipoCamb == 'Gestión':
            detalle = 'Ocs de gestión'
        
    
    return tipoCamb, SLA1, SLA2, detalle
        
def typeNov(row, dfT_Nov, dfT_Nov_Cat):
    '''
        Esta función permite determinar el tipo de novedad a partir de la descripción de la WO
        parameters:
            row: fila del dato a determinar
            dfT_Nov: dataframe que contiene los datos de tipo de novedad
        return:
            tupla: resultado de la busqueda
    '''
    #De la tabla TipoNovedad-Categoria se selecciona los datos que corresponden a la categoria
    dfT_Nov_Cat = dfT_Nov_Cat[dfT_Nov_Cat['Categoria OC'] == row['Oferta']]
    novData = re.search(r"Tipo de novedad(?:\s+\w+)?\s*:\s*([^\r\n]+)", row['Descripción'], re.IGNORECASE)
    #Traemos los datos por si no hay modificaciones dejarlos los valores por defecto
    typeCh, SLA_41, SLA_42, detail = row['Tipo de Cambio'], row['SLA_4.1'], row['SLA_4.2'], row['Detalle Categoria']
    if novData:
        novData = novData.group(1).strip()
        dfT_Nov = dfT_Nov[
            dfT_Nov['Tipo Novedad'].str.contains(novData, case=False, na=False, regex = False)
        ]
        if len(dfT_Nov) == 1:
            typeCh = dfT_Nov['Tipo Cambio'].iloc[0]
            if typeCh == 'Aprovisionamiento':
                detail = dfT_Nov['Aprovisionamiento de Recursos Nuevos (Compra de un Servidor Físico, Almacenamiento)'].str.contains(novData, case=False, na=False)
                if not detail.empty and len(detail) == 1:
                    detail = 'Aprovisionamiento de Recursos Nuevos (Compra de un Servidor Físico, Almacenamiento)'
                else:
                    detail = 'Aprovisionamiento de Recursos Existentes (Servidores, Cores, Memoria, Disco)'
                    
            elif typeCh == 'Desaprovisionamiento':
                detail = 'Ocs de Eliminación/Disminución Recursos'
                
            if len(dfT_Nov_Cat) >0:
                dfT_Nov_Cat = dfT_Nov_Cat[
                    dfT_Nov_Cat['Tipo Cambio'].str.contains(typeCh, case=False, na=False)
                ]
                if len(dfT_Nov_Cat) == 1:
                    SLA_41 = dfT_Nov_Cat['SLA (A partir de Marzo 2021)'].iloc[0]
                    SLA_42 = dfT_Nov_Cat['Medición KPI (anexo 4.2)'].iloc[0]
                         
    return typeCh, SLA_41, SLA_42, detail
