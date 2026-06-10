import pandas as pd
import numpy as np
import spacy
import re

#Se carga el mondelo en español de spacy
nlp = spacy.load('es_core_news_lg')

#Se crea una funcion para normalizar texto, pero vamos a conservar tildes
def normalizeText(text):
    if not isinstance(text, str):
        return text
    texto = text.strip().lower()
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def hybridSemanticSim(text1, text2):
    '''
        Esta función permite comparar de manera hibrida la semántica de dos textos:
        
        parameters:
            text1 (str): texto que se pretende comparar
            text2 (str): texto que se compara
        
        return
            result (float): similitud por token
    '''
    #definimos un diccionario para asignar pesos al tipo de comparación
    pesos = {
        'spacy': 0.2,
        'token': 0.15,
        'lema': 0.25,
        'verb': 0.4,
    }
    
    #Normalizamos los textos ingresados y genereamos los token de cada texto
    text1_nlp = nlp(normalizeText(text1))
    text2_nlp = nlp(normalizeText(text2))
    
    #Determinamos la magnitud por spacy tradiccional validando que se tengan valores por token
    simSCy = 0
    if text1_nlp.has_vector and text2_nlp.has_vector and text1_nlp.vector_norm > 0 and text2_nlp.vector_norm > 0:
        simSCy = text1_nlp.similarity(text2_nlp)
    
    #Determinamos la magnitud de similitud por token
    simToken = tokenSim(text1_nlp, text2_nlp)
    
    #Determinamos la magnitud de similitud por lema
    simLema = lemmaSim(text1_nlp, text2_nlp)
    
    #Determinamos la magnitud de similitud por verbo
    simVerb = verbSim(text1_nlp, text2_nlp)
    
    #Determinamos la similutd hibrida
    return (pesos['spacy']*simSCy + pesos['token']*simToken + pesos['lema']*simLema + pesos['verb']*simVerb)

def tokenSim(text1, text2):
    '''
        funcion que calcula similitud basada en la máxima similitud entre tokens individuales
        
        parameters:
            text1 (doc (spaCy)): texto a comparar
            text2 (doc (spaCy)): texto a comparar
            
        return
            result (float): similitud por token
    '''
    tokens_text1 = [t for t in text1 if not t.is_stop and not t.is_punct and t.has_vector]
    tokens_text2 = [t for t in text2 if not t.is_stop and not t.is_punct and t.has_vector]
    
    if not tokens_text1 or not tokens_text2:
        return 0.0
    
    similitudes = []
    for token1 in tokens_text1:
        maxTokenSim = 0
        for token2 in tokens_text2:
            if token1.has_vector and token2.has_vector:
                sim = token1.similarity(token2)
                maxTokenSim = max(maxTokenSim, sim)
        similitudes.append(maxTokenSim)
        
    return np.mean(similitudes) if similitudes else 0

def lemmaSim(text1, text2):
    '''
        esta funcion calcula similitud basada en lemas (raíces de palabras)
        
        parameters:
            text1 (doc (spaCy)): texto a comparar
            text2 (doc (spaCy)): texto a comparar
        
        return:
            value (float): valor de similitud por lemas
    '''
    
    #Separamos los textos por lemas
    lemas1 = {token.lemma_ for token in text1 if not token.is_stop and not token.is_punct and token.is_alpha}
    lemas2 = {token.lemma_ for token in text2 if not token.is_stop and not token.is_punct and token.is_alpha}
    
    if not lemas1 or not lemas2:
        return 0.0
    
    #Determinamos similitud tipo Jaccard
    interseccion = len(lemas1.intersection(lemas2))
    union = len(lemas1.union(lemas2))
    
    return interseccion / union if union > 0 else 0.0

def verbSim(text1, text2):
    '''
        Esta función calcula la similitud específica entre verbos
        
        parameters:
            text1 (doc (spaCy)): coleccion de token del texto a comparar
            text2 (doc (spaCy)): coleccion de token del texto a comparar
            
        return:
            value (float): resultado de calcular similitud
    '''
    
    #Determinamos los verbos en cada texto
    verbos1 = [token.lemma_ for token in text1 if token.pos_ == 'VERB']
    verbos2 = [token.lemma_ for token in text2 if token.pos_ == 'VERB']
    
    if not verbos1 or not verbos2:
        return 0.0
    
    # Si hay verbos idénticos, alta similitud
    verbos_comunes = set(verbos1).intersection(set(verbos2))
    if verbos_comunes:
        return 1.0
    
    # Si no, calcular similitud vectorial entre verbos
    max_sim = 0.0
    for verbo1 in verbos1:
        for verbo2 in verbos2:
            doc_v1 = nlp(verbo1)
            doc_v2 = nlp(verbo2)
            if doc_v1.has_vector and doc_v2.has_vector:
                sim = doc_v1.similarity(doc_v2)
                max_sim = max(max_sim, sim)
    
    return max_sim

def matchTasks_spacy(parameters, taskWork):
    tasksCatalog = pd.DataFrame()
    tasksCatalog['Tareas'] = parameters['Tareas']
    tasksCatalog['indices'] = parameters.index
    maxSimilitudes = []
    
    for taskSet in tasksCatalog['Tareas']:
        #Limipiamos tareas y dejamos un solo delimitador
        for delimiter in ['_ ', ' _', ' _ ', '__', '\\n','\n', '\n_', '\n_ ', '\t', '\t ', ' \t', '\t_', '\t_ ', '    ']:
            taskSet = taskSet.replace(delimiter, '_')
        taskSet = re.sub(r' {2,}', '_', taskSet)
        taskSet = [normalizeText(t) for t in re.split(r'[_]+',taskSet) if t.strip()]
        
        if len(taskSet)>0:
            maxSimil = 0
            for task in taskSet:
                sim = hybridSemanticSim(taskWork, task)
                if sim > maxSimil:
                    maxSimil = sim
                
            maxSimilitudes.append(maxSimil)
        
    tasksCatalog['maximos'] = maxSimilitudes
    maxValue = max(tasksCatalog['maximos'])
    
    if maxValue >= 0.7:
        return parameters.loc[tasksCatalog.loc[tasksCatalog['maximos'] == maxValue, 'indices'].tolist()]
    else:
        return parameters
    
def lemmaSimWO(text1, text2):
    '''
        esta funcion calcula similitud basada en lemas (raíces de palabras)
        
        parameters:
            text1 (doc (spaCy)): texto a comparar
            text2 (doc (spaCy)): texto a comparar
        
        return:
            value (float): valor de similitud por lemas
    '''
    text1 = nlp(normalizeText(text1))
    text2 = nlp(normalizeText(text2))
    #Separamos los textos por lemas
    lemas1 = {token.lemma_ for token in text1 if not token.is_stop and not token.is_punct and token.is_alpha}
    lemas2 = {token.lemma_ for token in text2 if not token.is_stop and not token.is_punct and token.is_alpha}
    
    if not lemas1 or not lemas2:
        return False
    
    #Determinamos similitud tipo Jaccard
    interseccion = len(lemas1.intersection(lemas2))
    union = len(lemas1.union(lemas2))
    
    if union > 0:
        if interseccion/ union > 0.7:
            return True
    return False