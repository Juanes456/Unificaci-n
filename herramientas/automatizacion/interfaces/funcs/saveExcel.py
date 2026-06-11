import xlwings as xw
import pandas as pd
import tkinter as tk
import re
import tkinter.filedialog as fd
import tkinter.messagebox as mb
from pathlib import Path

#Obtención de la ruta donde se encuentran los archivos 
def selecFile(entry):
    """
    Abre un cuadro de diálogo para seleccionar un archivo (Excel o CSV) 
    y actualiza un campo de entrada de texto de la UI con la ruta seleccionada.
    
    Args:
        entry (CTkEntry/Entry): Widget de entrada a actualizar.
    """
    file = fd.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
    
    if file:
        entry.delete(0, tk.END)
        entry.insert(0, file)

#Definimos una función que limpia el dataframe de caracteres que no permite excel
def cleanDataFrame(s):
    """
    Limpia cadenas de texto removiendo caracteres de control ASCII no permitidos por Excel.
    
    Args:
        s (any): El valor de la celda.
        
    Returns:
        any: El valor limpio de caracteres ilegales.
    """
    if isinstance(s,str):
        return re.sub(r'[\x00-\x1F]', "", s)
    return s

def saveExcelFile(dictDF,pathSave):
    """
    Escribe un conjunto de DataFrames agrupados en un diccionario en un archivo Excel.
    
    Valida el tipo de estructura del diccionario para escribir correctamente las hojas.
    Admite DataFrames directos o diccionarios con múltiples DataFrames impresos verticalmente.
    
    Args:
        dictDF (dict): Diccionario cuyas llaves representan nombres de hojas y valores representan DataFrames.
        pathSave (str): Ruta completa de destino donde se guardará el archivo Excel.
    """
    try:
        if not dictDF or not pathSave:
            raise ValueError('Parametros no válidos para guardar el archivo')
              
        with pd.ExcelWriter(pathSave, engine='openpyxl') as writer:
            for keyName, dfs in dictDF.items():
                if isinstance(dfs, pd.DataFrame):
                    # Filtrar caracteres de control ASCII en columnas de tipo objeto/texto
                    dfs = dfs.apply(lambda col: col.map(cleanDataFrame) if col.dtype == object else col)
                    dfs.to_excel(writer, index=False, sheet_name=keyName)
                elif isinstance(dfs, dict):
                    # Escritura secuencial en la misma pestaña con filas de separación
                    startRow = 0
                    for subKey, df in dfs.items():
                        titleDf = pd.DataFrame({subKey: [""]})
                        titleDf.to_excel(writer, index=False, sheet_name=keyName, startrow=startRow)
                        startRow += 1
                        df = df.apply(lambda col: col.map(cleanDataFrame) if col.dtype == object else col)
                        df.to_excel(writer, index=False, sheet_name=keyName, startrow=startRow)
                        startRow += len(df) + 3
                else:
                    raise ValueError('Tipo de dato no soportado')
                                
    except ValueError as ve:
        mb.showerror(title='Error', message=ve)
        
def saveExcelTemplate(dictDf, pathSave, intDate):
    """
    Vuelca datos de incidentes sobre una plantilla Excel pre-estilizada usando la interfaz COM xlwings.
    
    Configura el intervalo de fecha en la pestaña 'Inicio' y rellena la tabla
    estructurada 'dataTable' en la pestaña 'Data'.
    
    Args:
        dictDf (dict): Diccionario que contiene el DataFrame bajo la llave 'Data'.
        pathSave (str): Ruta final donde se almacenará la plantilla con los nuevos datos.
        intDate (str): Cadena de texto indicando el intervalo de fechas del reporte.
    """
    try:
        if not pathSave or not dictDf:
            raise ValueError('Parámetros no válidos para guardar el archivo')
        
        # Determinar la ruta relativa a la plantilla de Excel
        thisFile = Path(__file__).resolve().parent
        rootProyect = thisFile.parent.parent
        template = rootProyect / 'templates' / 'tmpFinishedIncident.xlsx'
        excel = xw.App(visible=False)
        wb = excel.books.open(template)
        # Escribir la fecha del reporte en la pestaña Inicio
        ws = wb.sheets['Inicio']
        ws.range((2,2)).value = intDate

        # Rellenar datos en la hoja Data
        ws = wb.sheets['Data']
        table = ws.api.ListObjects('dataTable')
        
        # Alinear encabezados del DataFrame con la cabecera de la tabla del Excel
        headers = [cell.Value for cell in table.HeaderRowRange]
        df = dictDf['Data']
        for col in headers:
            if col not in df.columns:
                df[col] = None
        
        df = df[headers]
        
        # Prevenir fallos en tablas vacías
        if df.shape[0] == 0:
            df.loc[0] = [None] * len(headers)
        
        # Limpiar los contenidos previos de la tabla dinámica
        if table.DataBodyRange is not None:
            table.DataBodyRange.ClearContents()
        
        # Obtener coordenadas de la celda de inicio
        table_range = ws.range(table.Range.Address)
        header_row = table_range.row
        header_col = table_range.column

        # Volcar los valores del DataFrame inmediatamente debajo de la cabecera
        start_row = header_row + 1  
        start_col = header_col
        ws.range((start_row, start_col)).options(index=False, header=False).value = df.values

        wb.save(pathSave)
    except ValueError as ve:
        print(ve)
        mb.showerror(title='Error', message=ve)
    finally:
        # Cerrar el libro y salir de Excel en segundo plano
        try:
            if wb is not None:
                wb.close()
        except Exception:
            pass
        
        try:
            if excel is not None:
                excel.quit()
        except Exception:
            pass
    