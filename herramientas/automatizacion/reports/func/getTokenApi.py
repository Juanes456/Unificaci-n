import os
import base64
import requests
import urllib3
import time
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Cargar las variables de entorno desde el archivo .env
load_dotenv()

def encryPass():
    '''
        Función que encripta la contraseña del usuario de Helix para poder ser enviada a la API de datos de Helix
        return:
            password (str): Contraseña desencriptada del usuario de Helix
            
    '''
    decode = base64.b64decode(os.getenv('ENCRYPASS').encode('utf-8'))
    return decode.decode('utf-8')

#Definimos una variable global para almacenar el token
_tokenCahe = {
    "token": None,
    "expire": 0
}

def login():
    '''
        Función que el login a la API de datos de HElix mediante el usuario y contraseña propocionados a TCS
        
        return:
            jwt (str): Token de acceso a la API de datos de Helix
    '''
    
    global _tokenCahe
    
    if _tokenCahe['token'] and time.time() < _tokenCahe['expire']:
        return _tokenCahe['token']
    
    body = {
        'username': os.getenv('USERAPI'),
        'password': encryPass()
    }
    
    Headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "*/*",
    }
    
    helixUrl = os.getenv('URLLOGHELIX')
    endpoint = os.getenv('URLENDPOINT')
    
    tokenResponse = requests.post(endpoint+helixUrl, headers=Headers, data=body, verify=False)
    _tokenCahe['token'] = tokenResponse.text
    _tokenCahe['expire'] = time.time() + 3590
    
    return tokenResponse.text