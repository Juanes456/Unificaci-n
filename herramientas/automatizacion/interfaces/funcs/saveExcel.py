import xlwings as xw
import pandas as pd
import tkinter as tk
import re
import tkinter.filedialog as fd
import tkinter.messagebox as mb
from pathlib import Path

#Obtención de la ruta donde se encuentran los archivos 
def selecFile(entry):
    file = fd.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
    
    if file:
        entry.delete(0, tk.END)
        entry.insert(0, file)

#Definimos una función que limpia el dataframe de caracteres que no permite excel
def cleanDataFrame(s):
    if isinstance(s,str):
        return re.sub(r'[\x00-\x1F]', "", s)
    return s

def saveExcelFile(dictDF,pathSave):
    '''
        Esta función permite el almacenadmiento de la información en un archivo Excel en la ruta con el nombre del archivo indicados, es importante aclarar que dentro del diccionario pueden haber diccionarios de dataframes por cada clave por lo que se hace dicha validación
        
        params:
            dictDF (dict): diccionario con dataframes
            pathSave (str): ruta de almacenamiento del excel
            
        return:
            None
    '''
    try:
        if not dictDF or not pathSave:
            raise ValueError('Parametros no válidos para guardar el archivo')
              
        with pd.ExcelWriter(pathSave, engine='openpyxl') as writer:
            for keyName, dfs in dictDF.items():
                if isinstance(dfs, pd.DataFrame):
                    dfs = dfs.apply(lambda col: col.map(cleanDataFrame) if col.dtype == object else col)
                    dfs.to_excel(writer, index=False, sheet_name=keyName)
                elif isinstance(dfs, dict):
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
    '''
        Esta funcion permite utilizar la plantilla de excel alojada en la carpeta templates generando un nuevo archivoexcel
        params:
            dictDf (str): diccionario con el dataframe que contiene los datos
            pathSave (str): ruta de almacenamiento del archivo
            intDate (str): intervalo de fecha para ponerlo en el objeto de la hoja incio
        
        return:
            None
    '''
    
    try:
        if not pathSave or not dictDf:
            raise ValueError('Parámetros no válidos para guardar el archivo')
        
        #Determinamos la ruta donde se encuentra la plantilla de excel
        thisFile = Path(__file__).resolve().parent
        rootProyect = thisFile.parent.parent
        template = rootProyect / 'templates' / 'tmpFinishedIncident.xlsx'
        excel = xw.App(visible=False)
        wb = excel.books.open(template)
        #Ponemos la fecha en la hoja inicio del documento
        ws = wb.sheets['Inicio']
        ws.range((2,2)).value = intDate

        #Agregamos los datos
        ws = wb.sheets['Data']
        table = ws.api.ListObjects('dataTable')
        
        #Reordenamos los encabezados del dataframe para que queden en el orden de la tabla
        headers = [cell.Value for cell in table.HeaderRowRange]
        df = dictDf['Data']
        for col in headers:
            if col not in df.columns:
                df[col] = None
        
        df = df[headers]
        
        #evitamos los casos en que el dataframe esté vacio
        if df.shape[0] == 0:
            df.loc[0] = [None] * len(headers)
        
        #Borra datos actuales de la tabla
        if table.DataBodyRange is not None:
            table.DataBodyRange.ClearContents()
        
        # Encuentra la celda superior izquierda de la tabla 
        table_range = ws.range(table.Range.Address)
        header_row = table_range.row
        header_col = table_range.column

        # Escribe los datos justo debajo de los encabezados
        start_row = header_row + 1  
        start_col = header_col
        ws.range((start_row, start_col)).options(index=False, header=False).value = df.values

        wb.save(pathSave)
    except ValueError as ve:
        print(ve)
        mb.showerror(title='Error', message=ve)
    finally:
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
    