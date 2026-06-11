import os
import locale
import tkinter.messagebox as mb
import tkinter.filedialog as fd
import interfaces.funcs.saveExcel as svEx
import interfaces.funcs.stylesExcel as stEx
from reports.reportCRQ import getReportCRQ
from reports.reportWO import getReportWO
from reports.reportSLA import getReportSLA
from reports.reportCMDB import getInsumoCMDB
from reports.reportOpenInc import getReportOpenInc
from reports.reportFinishInc import getReportFinishInc
from reports.validateSLA import validateSLA

locale.setlocale(locale.LC_TIME, 'es_Es.UFT-8')

def runProcess(initialDate, endDate, parameters, typeReport, getSLA=True, wo1=None, wo2=None):
    """
    Orquesta y ejecuta la generación de reportes dependiendo del tipo solicitado.
    
    Flujo:
    1. Valida que se hayan ingresado todos los parámetros obligatorios según el tipo de reporte.
    2. Utiliza un bloque match-case para delegar al generador de reporte correspondiente.
    3. Pregunta al usuario interactivamente dónde guardar el archivo Excel final mediante `fd.asksaveasfilename`.
    4. Escribe el archivo Excel, le aplica estilos visuales premium mediante `stEx.applyStyleExcel` y muestra una alerta de éxito.
    5. Si el usuario cancela la selección de ruta, el proceso aborta limpiamente sin errores.
    
    Args:
        initialDate (datetime): Fecha de inicio para el filtrado del reporte.
        endDate (datetime): Fecha final para el filtrado del reporte.
        parameters (str): Ruta al archivo de parámetros (Helix login, etc.).
        typeReport (str): El nombre del reporte (ej. 'Informe SLA', 'Informe WO', 'Informe CRQ', etc.).
        getSLA (bool): Flag opcional indicando si se calcula el SLA. Por defecto es True.
        wo1 (str): Ruta opcional del primer archivo de WO (días 1 al 15 del mes).
        wo2 (str): Ruta opcional del segundo archivo de WO (días 16 al 30 del mes).
    """
    try:
        # Validación inicial de parámetros
        is_incident_report = typeReport in ['Incidentes abiertos', 'Incidentes cerrados']
        if typeReport == "Informe WO" and (not wo1 or not wo2) or (not parameters and not is_incident_report):
            raise ValueError("No se ingresaron todos los parametros solicitados")
        elif not initialDate or not endDate or (not parameters and not is_incident_report) or not typeReport:
            raise ValueError("No se ingresaron todos los parametros solicitados")
        
        match typeReport:
            case 'Informe SLA':
                # Obtener mes en español para el nombre sugerido del archivo
                mes = initialDate.strftime("%B").capitalize()
                initial_file = f'Informe_SLA - {mes}.xlsx'
                # Solicitar ruta interactiva al usuario
                pathSave = fd.asksaveasfilename(
                    initialfile=initial_file,
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")]
                )
                if not pathSave:
                    return # Cancelado por el usuario
                
                # Ejecutar consulta y lógica del reporte SLA
                datos = getReportSLA(initialDate, endDate, parameters, wo1, wo2)
                svEx.saveExcelFile(datos, pathSave)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(pathSave)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {pathSave}")

            case 'Informe WO':
                # Ejecutar reporte de Órdenes de Trabajo (WO)
                datos = getReportWO(wo1, wo2, parameters, getSLA)
                filePath = fd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
                if not filePath:
                    return # Cancelado por el usuario
                svEx.saveExcelFile(datos, filePath)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(filePath)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                
            case 'Informe CRQ':
                # Ejecutar reporte de Cambios (CRQ)
                datos = getReportCRQ(initialDate, endDate, parameters, getSLA)
                filePath = fd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
                if not filePath:
                    return # Cancelado por el usuario
                svEx.saveExcelFile(datos, filePath)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(filePath)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                
            case 'Insumo CMDB':
                # Generar reporte de insumo CMDB
                datos = getInsumoCMDB(initialDate, endDate, wo1, wo2, parameters)
                filePath = fd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
                if not filePath:
                    return # Cancelado por el usuario
                svEx.saveExcelFile(datos, filePath)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(filePath)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                
            case 'Incidentes cerrados':
                # Generar reporte de incidentes cerrados (usa plantilla con ListObjects)
                datos = getReportFinishInc(initialDate, endDate, parameters)
                if not datos or datos.get("Data") is None or datos["Data"].empty:
                    raise ValueError('No hay datos para analizar (VPN inactiva o sin registros)')
                date = endDate.strftime("%d_%m_%Y")
                initial_file = f'Reporte_Incident_Cerrados - {date}.xlsx'
                pathSave = fd.asksaveasfilename(
                    initialfile=initial_file,
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")]
                )
                if not pathSave:
                    return # Cancelado por el usuario
                diaInicial = initialDate.day
                diafinal = endDate.day
                mesFinal = endDate.strftime('%b')
                intervalofecha = f'del {str(diaInicial)} al {str(diafinal)} de {mesFinal} del {str(initialDate.year)}'
                svEx.saveExcelTemplate(datos, pathSave, intervalofecha)
                mb.showinfo(title='Exito', message=f'El archivo se ha guardado correctamente en: {pathSave}')
                
            case 'Incidentes abiertos':
                # Generar reporte de incidentes abiertos
                datos = getReportOpenInc(initialDate, endDate, parameters)
                if not datos:
                    raise ValueError('No hay datos para analizar (VPN inactiva o sin registros)')
                date = endDate.strftime("%d_%m_%Y")
                initial_file = f'Reporte_Event_Incident_Abiertos - {date}.xlsx'
                pathSave = fd.asksaveasfilename(
                    initialfile=initial_file,
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")]
                )
                if not pathSave:
                    return # Cancelado por el usuario
                svEx.saveExcelFile(datos, pathSave)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(pathSave)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {pathSave}")
            
            case _:
                raise ValueError("Tipo de reporte desconocido")
        
    except ValueError as ve:
        mb.showerror(title="Error", message=ve)

def runValidateSLA(path):
    """
    Ejecuta el algoritmo de validación de SLAs sobre un archivo Excel de reportes generado previamente.
    
    Muestra la ruta resultante en un cuadro de diálogo para que el usuario elija exactamente
    dónde y bajo qué nombre desea almacenar los resultados validados.
    
    Args:
        path (str): Ruta completa al archivo Excel de origen (WO o CRQ) que se validará.
    """
    if not path:
        mb.showerror(title="Error", message="No se ha seleccionado un archivo para validar")
        
    else:
        datos = validateSLA(path)
        if not datos:
            mb.showerror(title="Error", message="No se encontraron registros para validar")
            raise ValueError("No se encontraron registros para validar")
        
        # Sugerir un nombre de archivo por defecto agregando el sufijo "_Validado"
        base, ext = os.path.splitext(path)
        initial_file = f'{os.path.basename(base)}_Validado{ext}'
        filePath = fd.asksaveasfilename(
            initialfile=initial_file,
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not filePath:
            return # Cancelado por el usuario
        svEx.saveExcelFile(datos, filePath)
        print('Archivo excel guardado exitosamente, ahora se aplican estilos')
        stEx.applyStyleExcel(filePath)
        mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                