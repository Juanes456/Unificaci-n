import pandas as pd
import os
from dotenv import load_dotenv
from reports.func.queryDataApi import queryData

#cargar las variables de entorno desde el archivo .env
load_dotenv()

def getActiveIncident(initialDate, endDate):
    '''
        Esta funcion permite generar el dataframe con los datos de inicidentes abiertos para un intervalo de fechas estipuladas por el usuario
        
        Parameters:
            intialDate (str): la fecha inicial del intervalo a consultar en el formato YYYY-MM-DD
            endDate (str): la fecha final del intervalo a consultar en el formato YYYY-MM-DD
            
        returns:
            dfWork (dataframe): datos de incidentes abiertos con filtros, modificaciones en el nombre de las columnas y las traducciones correspondites.
    '''
    #Definimos la url de la API de incidentes de Helix con sus respectivos filtros
    urlOpenIncidents = (
        f"{os.getenv('URLINC')}"
        f"fields=values(Incident Number,Service Type,TicketType,Priority,Original Incident Number,Status, SLM Status, Submit Date,Last Resolved Date,Assignee,Full Name,HPD_CI,Description,Assigned Group,Company)"
        f"&q= 'Submit Date' >= \"{initialDate}T05:00:00\" and 'Submit Date' <= \"{endDate}T05:00:00\" and ('Status' = \"Assigned\" or 'Status' = \"Pending\" or 'Status' = \"In Progress\")"
    )
    #Definimos la url para la consulta de los grupos de banco mediante BCO, con este podemos consultar la gerencia además del Direccion, Dominio y subdominio que para efectos de este reporte no se tiene en cuenta
    urlBCO = f"{os.getenv('URLBCO')}fields=values(Support Group Name,Support Organization)"

    #Traemos la lista de datos desde la api
    openIncidentData = queryData(urlOpenIncidents)
    bcoData = queryData(urlBCO)
    
    try:
        if len(openIncidentData)==0 or len(bcoData)==0:
            raise Exception('No se obtuvieron datos de la API')
        
        #Creamos los dataframes
        dfopenIncident = pd.DataFrame(openIncidentData)
        dfBCO = pd.DataFrame(bcoData)
        
        #Unificamos para trabajar solo con un dataframe
        dfWork = dfopenIncident.merge(
            dfBCO[['Support Group Name','Support Organization']],
            left_on='Assigned Group',
            right_on='Support Group Name',
            how='left'
        ).drop(columns=['Support Group Name'])
        
        #Renomabramos las columnas del dataframe
        dfWork = dfWork.rename(columns={
            'Incident Number': 'Ticket',
            'TicketType': 'Tipo de Caso',
            'Priority': 'Prioridad',
            'Original Incident Number': 'Incidente Padre',
            'Status': 'Estado',
            'Submit Date': 'Fecha Apertura',
            'Last Resolved Date': 'Fecha Resuelto',
            'Assignee': 'Asignado',
            'Full Name': 'Usuario Final Afectado',
            'SLM Status': 'Cumplimiento ANS',
            'HPD_CI': 'Instancia CI',
            'Description': 'Resumen',
            'Assigned Group': 'Grupo Asignado',
            'Company': 'Filial',
            'Department': 'Gerencia',
            'Support Organization': 'Gerencia'
        })
        
        #Eliminamos posibles tikects duplicados
        dfWork = dfWork.drop_duplicates(subset=['Ticket'])
        
        #Determinamos los eventos en el dataframe
        dfWork['Tipo de Caso'] = dfWork.apply(
            lambda row: row['Tipo de Caso'] if row['Service Type'] != 'Infrastructure Event' else 'Event',
            axis=1
        )
        
        #Eliminamos la columna de tipo de servicio
        dfWork.drop(columns=["Service Type"], inplace=True)
        
        #Damos el formato de fecha convirtiendo la data en la GTC-5 y eliminando la zona horaria
        dfWork["Fecha Apertura"] =  pd.to_datetime(dfWork['Fecha Apertura'], utc=True).dt.tz_convert('America/Panama').dt.tz_localize(None)
        dfWork["Fecha Resuelto"] =  pd.to_datetime(dfWork['Fecha Resuelto'], utc=True).dt.tz_convert('America/Panama').dt.tz_localize(None)
        
        #Traducimos valores de algunas columnas
        dfWork["Tipo de Caso"] = dfWork["Tipo de Caso"].replace({
            'Incident': 'Incidente',
            'Event': 'Evento'
        })
        
        dfWork["Prioridad"] = dfWork["Prioridad"].replace({
            'Medium': 'Media',
            'Low': 'Baja',
            'Critical': 'Crítica'
        })

        dfWork['Estado'] = dfWork['Estado'].replace({
            'Assigned': 'Asignado',
            'Pending': 'Pendiente',
            'In Progress': 'En progreso'
        })
        
        dfWork['Cumplimiento ANS']= dfWork['Cumplimiento ANS'].replace({
            'Service Targets Breached': 'Objetivo de servicio incumplido',
            'Within the Service Target': 'Dentro del objetivo de servicio',
            'Service Target Warning': 'Advertencia del objetivo de servicio'
        })
        print(f'Consulta de incidentes abiertos finalizada con {len(dfWork)} registros')
        return dfWork
        
    except Exception as e:
        print(f'Error: {e}')    
        return pd.DataFrame()

def getFinalizedIncident(initialDate, endDate):
    '''
        Esta funcion permite generar el dataframe con los datos de inicidentes cerrados para un intervalo de fechas estipuladas por el usuario.
        Parameters:
            intialDate (str): la fecha inicial del intervalo a consultar en el formato YYYY-MM-DD
            endDate (str): la fecha final del intervalo a consultar en el formato YYYY-MM-DD
        returns:
            dfWork (dataFrame): un dataframe con los datos de incidentes cerrados
    '''
    
    #Definimos las url de la API de incidentes cerrado de Helix con sus respectivos filtros
    urlFinalizedIncidents = (
        f"{os.getenv('URLINC')}"
        "fields=values(Incident Number,Service Type,TicketType,Priority,Original Incident Number,Status, SLM Status, Submit Date,Last Resolved Date,Assignee,Full Name,HPD_CI,Description,Assigned Group,Company)"
        f"&q= 'Service Type' != \"Infrastructure Event\" and 'SLM Status' != \"Service Target Warning\" and ('Status' = \"Resolved\" or 'Status' = \"Closed\" or 'Status' = \"Cancelled\") and 'Last Resolved Date' >= \"{initialDate}T05:00:00\" and 'Last Resolved Date' <= \"{endDate}T05:00:00\""
    )
    
    urlBCO = f"{os.getenv('URLBCO')}fields=values(Support Group Name,Support Organization)"
    
    #Traemos la lista de datos desde la api
    finalizedIncidentData = queryData(urlFinalizedIncidents)
    bcoData = queryData(urlBCO)
    
    try:
        if len(finalizedIncidentData)==0 or len(bcoData)==0:
            raise ValueError('No se obtuvieron datos de la API')
        #Creamos los dataframes
        dfFinalizedIncident = pd.DataFrame(finalizedIncidentData)
        dfBCO = pd.DataFrame(bcoData)
        
        #Unificamos para trabajar solo con un dataframe
        dfWork = dfFinalizedIncident.merge(
            dfBCO[['Support Group Name','Support Organization']],
            left_on='Assigned Group',
            right_on='Support Group Name',
            how='left'
        ).drop(columns=['Support Group Name'])
        
        #Renomabramos las columnas del dataframe
        dfWork = dfWork.rename(columns={
            'Incident Number': 'Ticket',
            'TicketType': 'Tipo de Caso',
            'Priority': 'Prioridad',
            'Original Incident Number': 'Incidente Padre',
            'Status': 'Estado',
            'SLM Status': 'Cumplimiento ANS',
            'Submit Date': 'Fecha Apertura',
            'Last Resolved Date': 'Fecha Resuelto',
            'Assignee': 'Asignado',
            'Full Name': 'Usuario Final Afectado',
            'HPD_CI': 'Instancia CI',
            'Description': 'Resumen',
            'Assigned Group': 'Grupo Asignado',
            'Company': 'Filial',
            'Subdomain': 'Subdominio',
            'Support Organization': 'Subdominio'
        })
        
        #Eliminamos posibles tikects duplicados
        dfWork = dfWork.drop_duplicates(subset=['Ticket'])
        
        #Eliminamos la columna de tipo de servicio
        dfWork.drop(columns=["Service Type"], inplace=True)
        
        #Damos el formato de fecha convirtiendo la data en la GTC-5 y eliminando la zona horaria
        dfWork["Fecha Apertura"] = pd.to_datetime(dfWork['Fecha Apertura'], utc=True).dt.tz_convert('America/Panama').dt.tz_localize(None)
        dfWork["Fecha Resuelto"] = pd.to_datetime(dfWork['Fecha Resuelto'], utc=True).dt.tz_convert('America/Panama').dt.tz_localize(None)
        
        #Traducimos valores de algunas columnas
        dfWork["Tipo de Caso"] = dfWork["Tipo de Caso"].replace({
            'Incident': 'Incidente'
        })
        
        dfWork["Prioridad"] = dfWork["Prioridad"].replace({
            'Medium': 'Media',
            'Low': 'Baja',
            'Critical': 'Crítica'
        })
        
        dfWork['Estado'] = dfWork['Estado'].replace({
            'Resolved': 'Resuelto',
            'Closed': 'Cerrado',
            'Cancelled': 'Cancelado'
        })
        
        dfWork['Cumplimiento ANS'] = dfWork['Cumplimiento ANS'].replace({
            'Service Targets Breached': 'Objetivo de servicio incumplido',
            'Within the Service Target': 'Dentro del objetivo de servicio'
        })
        
        #Cambiamos el nombre de bancolombia panamá
        dfWork['Filial'] = dfWork['Filial'].replace({
            'BANCOLOMBIA PANAMÁ S.A.': 'BANISTMO S.A.'
        })
        print(f'Consulta de incidentes cerrados con {len(dfWork)} registros')
        return dfWork

    except ValueError as e:
        print(f'Error: {e}')
        return pd.DataFrame()

def getCRQs(initialDate, endDate):
    '''
        Esta función permite la obtención de CRQs desde la api, hay que tener presente que las CRQs y las tareas se encuentran en dos tableros diferente por lo que inicialmente se trae la data de CRQs y por medio de la llave se trae las tareas respectivas para posteriormente generar un merge
        
        parameters:
            initialDate (str): fecha inicial del informe
            endDate (str): Fecha final del informe
        
        return:
            dfWork (DataFrame): datos de CRQs
    '''
    
    #Construimos la url que permite la consulta por tareas
    urlTask = (
        f'{os.getenv('URLTASK')}'
        'fields=values(RootRequestID, Sequence, Task ID, TaskName, Summary, Assignee, Assignee Group, Status, StatusReasonSelection, Actual Start Date, Actual End Date, Last Modified By, Scheduled Start Date, Scheduled End Date, Assign Time, Activate Time, End Time, Duration in Minutes) &q= '
        f" 'End Time' >= \"{initialDate}T05:00:00\" and 'End Time' <= \"{endDate}T05:00:00\" and 'Status' = \"Closed\" "
    )
    
    #Traemos la data de la api
    print('Consultando tareas desde la API...')
    taskData = queryData(urlTask)
    #Creamos una lista con valores unicos para obtener el nombre de la ultima persona en modificar la tarea
    uniqueLastModified = list(
        {task['Last Modified By'] for task in taskData}
    )
    #Consultamos los nombres
    urlCTM = (
        f'{os.getenv('URLCTM')}'
        'fields=values(Full Name, Remedy Login ID)&q= '
    )
     
    listCTM = []
    for i in range(0, len(uniqueLastModified), 50):
        batch = uniqueLastModified[i:i+50]
        urlQueryCTM = 'or'.join([f" 'Remedy Login ID' = \"{id}\" " for id in batch])
        listCTM.extend(queryData(urlCTM + urlQueryCTM, False))
    print('Finalizo la consulta de tareas, ahora se consultan las CRQs...')
    
    try:
        #Verificamos que la consulta a la api traiga valores
        if len(taskData) == 0:
            raise ValueError('No se obturvieron tareas desde la API')
        
        #Construimos el dataframe
        dfTask = pd.DataFrame(taskData)
        dfCTM = pd.DataFrame(listCTM)
        
        #Eliminamos posibles duplicados
        dfTask.drop_duplicates(subset=['Task ID'], inplace=True)
        
        #Unificamos los dataframes
        dfTask = dfTask.merge(
            dfCTM,
            left_on='Last Modified By',
            right_on='Remedy Login ID',
            how='left'
        ).drop(columns=['Remedy Login ID', 'Last Modified By'])
        
        #Reenomabramos una columna para evitar problemas en el merge
        dfTask.rename(columns={'Actual End Date': 'Hora Fin Tarea', 'Scheduled Start Date': 'Hora Inicio Programada Tarea', 'Scheduled End Date': 'Hora Fin Programada Tarea',}, inplace=True)
        
        #Construimos la url para la consulta de la CRQ respectiva
        urlCRQs = (
            f'{os.getenv('URLCRQ')}'
            'fields=values(Infrastructure Change ID, z1D_Template_Name, Change Request Status, Risk Level, Description, Detailed Description, Reason For Change, Status Reason, Submit Date, Last Modified Date, Actual End Date, Scheduled Start Date, Scheduled End Date, ASCHG, ASGRP, Company3, Priority) &q= '
        )
        
        listCRQs = []
        #Se hace la consulta a la API y se trae las tareas evitando url demasiado largas para el servidor
        for i in range(0, len(dfTask), 70):
            batch = list(dfTask['RootRequestID'].iloc[i:i+70])
            urlQueryCRQ = 'or'.join([f" 'Infrastructure Change ID' = \"{Id}\" " for Id in batch])
            listCRQs.extend(queryData(urlCRQs + urlQueryCRQ, False))
        
        #Creamos el dataframe
        dfCRQs = pd.DataFrame(listCRQs)
        
        if len(dfCRQs)==0:
            raise ValueError('No se han obtenido CRQs')
        
        #Eliminamos posibles duplicados en el ID de la CRQ y unificamos los dataframes
        dfCRQs.drop_duplicates(subset=['Infrastructure Change ID'], inplace=True)
        
        #Creamos el dataframe de trabajo unificando las tareas y CRQs relacionada
        dfWork = pd.merge(dfCRQs, dfTask, left_on='Infrastructure Change ID', right_on='RootRequestID', how='left').drop(columns=['RootRequestID'])
        
        #Cambiamos los nombres de las columnas
        dfWork = dfWork.rename(columns={
            'Infrastructure Change ID': 'Codigo Orden',
            'z1D_Template_Name': 'Categoria',
            'Change Request Status': 'Estado',
            'Risk Level': 'Nivel de Riesgo',
            'Description': 'Resumen',
            'Detailed Description': 'Descripcion',
            'Reason For Change': 'Razon Del Cambio',
            'Status Reason': 'Razon de Estado',
            'Submit Date': 'Fecha Creacion CRQ',
            'Last Modified Date': 'Ultima Modificacion',
            'Actual End Date': 'Fecha Cierre CRQ',
            'Scheduled Start Date': 'Fecha inicio programada',
            'Scheduled End Date': 'Fecha fin programada',
            'ASCHG': 'Coordinador Cambio',
            'ASGRP': 'Grupo coordinador',
            'Company3': 'Filial',
            'Priority': 'Prioridad',
            'Sequence': 'Secuencia',
            'Task ID': 'Codigo Tarea',
            'TaskName': 'Tarea',
            'Summary': 'Resumen Tarea',
            'Assignee': 'Asignado',
            'Assignee Group': 'Grupo Asignado',
            'Status': 'Estado Tarea',
            'StatusReasonSelection': 'Motivo Del Estado',
            'Actual Start Date': 'Hora Inicio Tarea',
            'Full Name': 'Nombre Cerro Tarea',
            'Assign Time': 'Tiempo Asignado',
            'Activate Time': 'Inicio Tarea Sistema',
            'End Time': 'Cerro Tarea Sistema',
            'Duration in Minutes': 'Duracion en minutos'
        })
        #Eliminamos duplicados por tareas
        dfWork.drop_duplicates(subset=['Codigo Tarea'], inplace=True)
        
        #Damos formato de fechas a las columnas respectivas
        dateColumns = ['Fecha Creacion CRQ', 'Fecha Cierre CRQ', 'Fecha inicio programada', 'Fecha fin programada', 'Ultima Modificacion', 'Hora Inicio Programada Tarea', 'Hora Fin Programada Tarea', 'Hora Inicio Tarea', 'Hora Fin Tarea', 'Tiempo Asignado', 'Inicio Tarea Sistema', 'Cerro Tarea Sistema']
        
        for col in dateColumns:
            dfWork[col] = pd.to_datetime(dfWork[col], utc=True).dt.tz_convert('America/Panama').dt.tz_localize(None)
        
        #Damos formato a otras columnas
        dfWork['Secuencia'] = dfWork['Secuencia'].astype(float)
        dfWork['Duracion en minutos'] = dfWork['Duracion en minutos'].astype(float)
        
        #Traducimos al español algunos datos
        dfWork['Estado']=dfWork['Estado'].replace({
            'Closed': 'Cerrado',
            'Cancelled': 'Cancelado',
            'Completed': 'Completado',
            'Rejected': 'Rechazado',
            'Scheduled': 'Programado',
            'Implementation In Progress': 'Implementacion en curso'
        })
        
        dfWork['Nivel de Riesgo'] = dfWork['Nivel de Riesgo'].str.replace(
            r'Risk Level (\d+)',
            r'Nivel de Riesgo \1',
            regex=True
        )
        
        dfWork['Razon Del Cambio'] = dfWork['Razon Del Cambio'].replace({
            'Fix/Repair': 'Arreglar/Reparar',
            'New Functionality': 'Nueva Funcionalidad',
            'Maintenance': 'Mantenimiento',
            'Upgrade': 'Actualizar',
            'No Longer Required': 'No es necesario',
            'To Be Re-Scheduled': 'Reprogramar',
            'Other': 'Otro'
        })
        
        dfWork['Razon de Estado'] = dfWork['Razon de Estado'].replace({
            'Successful': 'Con éxito',
            'Resources Not Available': 'Sin éxito',
            'Final Review Complete': 'Cerrado Automáticamente',
            'Unsuccessful' : 'Sin éxito',
            'Backed Out': 'Retirado',
            'Automatically Closed': 'Cerrado automáticamente',
            'Successful with Issues': 'Exitoso con problemas'
        })
        
        dfWork['Estado Tarea'] = dfWork['Estado Tarea'].replace({
            'Closed': 'Cerrada',
        })
        
        dfWork['Motivo Del Estado'] = dfWork['Motivo Del Estado'].replace({
            'Success': 'Satisfactorio',
            'Cancelled': 'Cancelado',
            'Assignment': 'Encargado',
            'Failed': 'Fallido'
        })
        
        dfWork['Prioridad'] = dfWork['Prioridad'].replace({
            'Low': 'Baja',
            'High': 'Alta',
            'Critical': 'Crítica'
        })
        print(f'Consulta de CRQs finalizada con {len(dfWork)} registros')
        return dfWork
    except ValueError as ve:
        print(f'Error: {ve}')
        return pd.DataFrame()
    
def getWOs(initialDate, endDate):
    '''
        Esta funcion permite traer los datos de las WOs desde la API en un intervalo temporal
        
        parameters:
            initialDate (str): fecha inicial a consultar los datos
            endaDate (str): fecha final a consultar los datos
            
        return:
            dfWork (DataFrame): datos depurados
    '''
    
    #Construimos la URL que permite la consulta de las WO
    urlWO = (
        f"{os.getenv('URLWOS')}"
        'fields=values()'
    )
    
    print('Pendiente permisos de consulta de tabla oferta de WOs!!!')
    