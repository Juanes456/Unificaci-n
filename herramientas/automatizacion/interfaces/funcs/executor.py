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
    '''
        Esta función ejecuta el proceso de generación de reportes, dependiendo del tipo de reporte solicitado.
        parameters:
            initialDate (datetime): Fecha inicial del reporte
            endDate (datetime): Fecha final del reporte
            parameters (str): ruta donde se encuentra el archivo de parametros
            typeReport (str): Tipo de reporte que se desea generar (e.g., "Incidentes abiertos", "CRQs", etc.)
            getSLA (bool): Indica si se desea calcular el SLA, por defecto es True
            wo1 (str): Ruta del archivo de WOs del 1 al 15 del mes, por defecto es None
            wo2 (str): Ruta del archivo de WOs del 16 al 30 del mes, por defecto es None
    '''
    try:
        is_incident_report = typeReport in ['Incidentes abiertos', 'Incidentes cerrados']
        if typeReport == "Informe WO" and (not wo1 or not wo2) or (not parameters and not is_incident_report):
            raise ValueError("No se ingresaron todos los parametros solicitados")
        elif not initialDate or not endDate or (not parameters and not is_incident_report) or not typeReport:
            raise ValueError("No se ingresaron todos los parametros solicitados")
        
        match typeReport:
            case 'Informe SLA':
                mes = initialDate.strftime("%B").capitalize()
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                pathSave = os.path.join(desktop,f'Informe_SLA - {mes}.xlsx')
                datos = getReportSLA(initialDate, endDate, parameters, wo1, wo2)
                svEx.saveExcelFile(datos, pathSave)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(pathSave)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {pathSave}")

            case 'Informe WO':
                datos = getReportWO(wo1, wo2, parameters, getSLA)
                filePath = fd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
                svEx.saveExcelFile(datos, filePath)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(filePath)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                
            case 'Informe CRQ':
                datos = getReportCRQ(initialDate, endDate, parameters, getSLA)
                filePath = fd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
                svEx.saveExcelFile(datos, filePath)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(filePath)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                
            case 'Insumo CMDB':
                datos = getInsumoCMDB(initialDate, endDate, wo1, wo2, parameters)
                filePath = fd.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
                svEx.saveExcelFile(datos, filePath)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(filePath)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                
            case 'Incidentes cerrados':
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
                    return
                diaInicial = initialDate.day
                diafinal = endDate.day
                mesFinal = endDate.strftime('%b')
                intervalofecha = f'del {str(diaInicial)} al {str(diafinal)} de {mesFinal} del {str(initialDate.year)}'
                svEx.saveExcelTemplate(datos, pathSave, intervalofecha)
                mb.showinfo(title='Exito', message=f'El archivo se ha guardado correctamente en: {pathSave}')
                
            case 'Incidentes abiertos':
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
                    return
                svEx.saveExcelFile(datos, pathSave)
                print('Archivo excel guardado exitosamente, ahora se aplican estilos')
                stEx.applyStyleExcel(pathSave)
                mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {pathSave}")
            
            case _:
                raise ValueError("Tipo de reporte desconocido")
        
    except ValueError as ve:
        mb.showerror(title="Error", message=ve)

def runValidateSLA(path):
    '''
        Esta función ejecuta el proceso de validación de SLA para los reportes de CRQ y WO.
        Parameters:
            path (str): Ruta del archivo de reporte a validar
    '''
    if not path:
        mb.showerror(title="Error", message="No se ha seleccionado un archivo para validar")
        
    else:
        datos = validateSLA(path)
        if not datos:
            mb.showerror(title="Error", message="No se encontraron registros para validar")
            raise ValueError("No se encontraron registros para validar")
        
        base, ext = os.path.splitext(path)
        filePath = f'{base}_Validado{ext}'
        svEx.saveExcelFile(datos, filePath)
        print('Archivo excel guardado exitosamente, ahora se aplican estilos')
        stEx.applyStyleExcel(filePath)
        mb.showinfo(title="Estilos aplicados", message=f"Se ha generado el archivo correctamente en: {filePath}")
                