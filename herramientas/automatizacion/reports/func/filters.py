import pandas as pd
import unicodedata as udd

def filters(row):
    if pd.isna(row['Eliminar']):
        
        #Si el campo del asignado esta vacio
        if pd.isna(row['Asignado']) or row['Asignado'] == '':
            #Si el campo del Grupo Asignado esta vacio
            if pd.isna(row['Grupo Asignado']) or row['Grupo Asignado'] == '':
                return '1. Sin usuario asignado y sin grupo asignado'
            #Si el campo del Grupo NO esta vacio pero el Torre Grupos si lo esta
            elif pd.isna(row['Torre Grupos']) or row['Torre Grupos'] == '':
                return '2. Sin usuario asignado y grupo no TCS'
        #Si el campo Asignado NO esta vacio pero si el de torre asignado
        elif pd.isna(row['Torre Asignado TCS']) or row['Torre Asignado TCS'] == '':
            return '3. Usuario asignado no TCS'
        
        #Verificamos que la columna Estado es cancelado y en motivo del estado se cancelo
        if row['Estado'] == 'Cancelado' and row['Motivo Del Estado'] == 'Cancelado':
            return "4. CRQ y Tarea Cancelada"
        
        #Verificamos que en la columan Motivo del estado se cancelo y que el tiempo de ejecucion de la tarea sea 0
        # if row['Motivo Del Estado'] == 'Cancelado' and (row['Hora Inicio Tarea'] == row['Hora Fin Tarea'] or pd.isna(row['Duracion en minutos'])):
        #     return "5. Tarea Cancelada"
        if row['Motivo Del Estado'] == 'Cancelado' and pd.isna(row['Duracion en minutos']):
            return "5. Tarea Cancelada"
        
        #Verificamos si en la columna tarea hay tareas alucivas a validar, actualizar, etc.
        if keyFilter(row):
            return "6. Tareas de validación y análisis"
            
        #Validamos si el asignado pertenece a agile
        if "agile" in str(row['Torre Asignado TCS']).strip().lower():
            return "7. Asignado pertenece a Agile"
        
        #verificamos si hay Llamadas de Analista
        if callFilter(row):
            return "8. Llamadas del analista"
        
        #Verificamos si la CRQ tiene tarea
        if pd.isna(row['Tarea']):
            return '9. Petición sin tarea'
        return None
    
def keyFilter(row, columnName='Tarea'):
    
    if pd.isna(row['Eliminar']):
        # Lista de patrones clave (sin tildes ni errores)
        keywords = ['validacion', 'analizar', 'analisar', 'actualizar', 'actualisar', 'revisar', 'analisis', 'validar', 'grupo ejecutor']
        non_keywords = ['cmdb', 'paquetes', 'elemento', '- implementacion']
        
        #Organizamos el texto de la columna tarea ortografia y quitamos tíldes
        task = row[columnName]
        if not isinstance(task, str):
            return ''
        
        #normalizamos el texto eliminando tildes y poniendo las tareas en minusculas
        task = udd.normalize('NFKD', task).encode('ascii', 'ignore').decode('utf-8')
        task = task.lower()
        
        #Verificamos si la tarea es aluciva a algunas palabras claves
        inkeywords = any(keyword in task for keyword in keywords)
        notinkeywords = all(non_keyword not in task for non_keyword in non_keywords)
        
        return inkeywords and notinkeywords
    
def callFilter(row):
    if pd.isna(row['Eliminar']):
        # Lista de patrones clave (sin tildes ni errores)
        keywords = ['Llamada', 'analista']
        
        #Organizamos el texto de la columna tarea ortografia y quitamos tíldes
        task = row['Tarea']
        if not isinstance(task, str):
            return ''
        
        task = udd.normalize('NFKD', task).encode('ascii', 'ignore').decode('utf-8')
        task = task.lower()
        
        #Verificamos si la tarea es aluciva a algunas palabras claves
        inkeywords = any(keyword in task for keyword in keywords)
        
        return inkeywords 

#Filtros para las WO
def filtersWO(row):
    if pd.isna(row['Eliminar']):
        if pd.notna(row['SecuenciaTarea']):
            if pd.isna(row['UsuarioAsignado']) or row['UsuarioAsignado'] == '':
                if pd.isna(row['Grupoasignadotarea']) or row['Grupoasignadotarea'] == '':
                    return '8. Tarea sin usuario asignado y sin grupo asignado'
                elif pd.isna(row['Torre Grupos x Task']) or row['Torre Grupos x Task'] == '':
                    return '1. Sin usuario asignado y grupo no TCS'
            elif pd.isna(row['Torre Asignado x Task']) or row['Torre Asignado x Task'] == '':
                return '2. Usuario asignado no TCS'
        elif pd.isna(row['Analistadecapacidadasignado']) or row['Analistadecapacidadasignado'] == '':
            if pd.isna(row['GrupoCapacidadAsignado']) or row['GrupoCapacidadAsignado'] == '':
                return '7. WO sin usuario asignado y sin grupo asignado'
            elif pd.isna(row['Torre Grupos x WO']) or row['Torre Grupos x WO'] == '':
                return '1. Sin usuario asignado y grupo no TCS'
        elif pd.isna(row['Torre Asignado x WO']) or row['Torre Asignado x WO'] == '':
            return '2. Usuario asignado no TCS'
        
        if pd.isna(row['SecuenciaTarea']):
            if row['EstadoCaso'] == 'Cancelado':
                return '3. WO Cancelada'
            if keyFilter(row, 'ResumenWO'):
                return '6. Tareas de validación y análisis'
        else:
            if row['RazondeEstado'] == 'Se canceló' and (pd.isna(row['MinutosDuracion']) or row['MinutosDuracion'] == ''):
                return '4. Tarea Cancelada'
            if keyFilter(row, 'NombreTarea'):
                return '6. Tareas de validación y análisis'
            
        if 'agile' in str(row['Torre Asignado x Task']).strip().lower() or 'agile' in str(row['Torre Asignado x WO']).strip().lower():
            return '7. Asignado pertenece a Agile'

        if row['EstadoCaso'] == 'Cancelado' and row['RazondeEstado'] == 'Se canceló':
            return '5. WO y Tarea Cancelada'
        