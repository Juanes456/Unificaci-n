import os
import requests

from dotenv import load_dotenv
from reports.func.getTokenApi import login

#cargar las variables de entorno desde el archivo .env
load_dotenv()

def queryData(url, showPag = True):
    '''
        Mediante esta función consultamos los datos de la api para obtener los datos respectivos a la url ingresada
        parameters:
            url (str): ruta de consulta de la API
        return:
            datos (list) : lista de datos obtenidos de la API de Helix
    '''
    
    #Obtenemos el token de acceso a la API de datos de Helix
    token = login()
    
    #Obtenemos el endpoint
    endpoint = os.getenv('URLENDPOINT')
    
    #Definimos el payload y los headers para la solicitud a la API
    payload = {}
    headers = {
        'Authorization': f'AR-JWT {token}'
    }
    
    #Definimos la lista de datos que almacenara los datos obtenidos de la API
    data = []
    
    #Realizamos la solicitud a la API
    try:
        #Definimos parametros de paginacion de la consulta API, limit el numero de registros a obtener por página y offset el inicio de la paginación
        limit = 1000
        offset = 0
        while True:
            if url.startswith("http://") or url.startswith("https://"):
                pageURL = f'{url}&limit={limit}&offset={offset}'
            else:
                pageURL = f'{endpoint}{url}&limit={limit}&offset={offset}'
            #Consulta GET
            response = requests.get(pageURL, headers=headers, data=payload, verify= True)
            if response.status_code != 200:
                raise ValueError(f"Error al consultar la API: {response.status_code} - {response.text}")
            
            datosJSON = response.json()
            
            #Terminamos el ciclo si no hay más entradas
            if not datosJSON.get('entries'):
                if showPag:
                    print(f'num_Pag: {int((offset/limit)+1)}')
                break
            
            #Agregamos los datos obtenidos a la lista de datos
            for entry in datosJSON['entries']:
                data.append(entry['values'])
                
            #Aumentamos el offset para la siguiente página
            offset += limit
        
        return data
            
    except ValueError as ve:
        print(f'Error: {ve}')
        return []
    
    except Exception as e:
        print(f'Error detallado de conexión: {e}')
        print('Error: Verifica que la VPN de Bancolombia esté activada')
        return []
    
 
        
