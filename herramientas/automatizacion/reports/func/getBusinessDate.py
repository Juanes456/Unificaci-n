import datetime as dt
import holidays as hd
import re

def isBusinessDay(date: dt.date, holidays: set, country: str):
    '''
        Esta función verifica si una fecha es un día hábil.
        Parameters:
            date (dt.date): Fecha a verificar
            holidays (set): Conjunto de días festivos
        Returns:
            bool: True si es un día hábil, False en caso contrario
    '''
    #Dependiendo del pais determinamos si es un día hábil
    if country == 'PA' and date.weekday() >= 5:
        return False
    if country == 'CO' and date.weekday() == 6:
        return False
    #Si es un día festivo, no es día hábil
    if date in holidays:
        return False
    return True

def getBusinessHours(date: dt.datetime, country: str):
    '''
        Esta función obtiene las horas hábiles de un día específico.
        Parameters:
            date (dt.datetime): Fecha a verificar
            country (str): País para determinar las horas hábiles
        Returns:
            tuple: Horas de inicio y fin del día hábil
    '''
    if country == 'PA' and date.weekday() in range(0,5):
        return (dt.time(6, 0), dt.time(18, 0))
    elif country == 'CO':
        if date.weekday() in range(0,5):
            return (dt.time(8, 0), dt.time(18, 0))
        elif date.weekday() == 5:
            return (dt.time(8, 0), dt.time(14, 0))
    return (None, None)

def nextBusinessDay(date: dt.datetime, holidays: set, country: str):
    '''
        Esta función obtiene el siguiente día hábil a partir de una fecha dada.
        Parameters:
            date (dt.datetime): Fecha inicial
            holidays (set): Conjunto de días festivos
            country (str): País para determinar los días hábiles
        Returns:
            dt.datetime: Siguiente día hábil
    '''
    #Determinamos si el siguiente día es un día hábil
    nextDate = dt.timedelta(days=1)
    while True:
        date += nextDate
        if isBusinessDay(date.date(), holidays, country):
            start, _ = getBusinessHours(date, country)
            return date.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
            
def limitDate(start_date: dt.datetime, sla: str, bank: str):
    '''
        Esta función calcula la fecha límite para un SLA dado un tiempo en horas y considearando los días hábiles.
        Parameters:
            start_date (dt.datetime): Fecha de inicio del SLA
            hours (int): Horas de SLA
            bank (str): Banco (Bancolombia o Banismo)
        Returns:
            dt.datetime: Fecha límite de cumplimiento del SLA
    '''
    # Determinamos los días feriados en Colombia o Panamá y se tiene encuenta el cambio de año
    years = set([start_date.year, start_date.year + 1])
    country = 'CO' if 'bancolombia' in bank.lower() else ('PA' if 'banistmo' in bank.lower() else None)
    countryHolidays = set()
    
    if not country:
        return None
    
    for y in years:
        countryHolidays.update(hd.country_holidays(country, years=[y]).keys())

    currentDate = start_date
    sla = extracTime(sla)
    if not sla:
        return None
    remainingHours = sla[0]
    #Si SLA no es día hábil, entonces sólo sumamos las horas 
    if not sla[1]:
        currentDate += dt.timedelta(hours=remainingHours)
    
    while remainingHours > 0 and sla[1]:
        #Si no es día hábil, saltamos al siguiente día
        if not isBusinessDay(currentDate.date(), countryHolidays, country):
            currentDate = nextBusinessDay(currentDate, countryHolidays, country)
            continue
        
        businessHours = getBusinessHours(currentDate.date(), country)
        if not businessHours:
            currentDate = nextBusinessDay(currentDate, countryHolidays, country)
            continue
        
        startTime, endTime = businessHours
        startDay = currentDate.replace(hour=startTime.hour, minute=startTime.minute, second=0, microsecond=0)
        endDay = currentDate.replace(hour=endTime.hour, minute=endTime.minute, second=0, microsecond=0)
        
        # Si estamos antes del inicio de jornada, movernos al inicio
        if currentDate < startDay:
            currentDate = startDay

        # Si estamos después del fin de jornada, movernos al próximo día hábil
        if currentDate >= endDay:
            currentDate = nextBusinessDay(currentDate, countryHolidays, country)
            continue

        # Calcular cuántas horas hábiles quedan en el día
        delta = (endDay - currentDate).total_seconds() / 3600.0
        if remainingHours <= delta:
            # Podemos terminar hoy
            currentDate += dt.timedelta(hours=remainingHours)
            return currentDate
        else:
            # Consumimos el resto del día y seguimos
            currentDate = nextBusinessDay(currentDate, countryHolidays, country)
            remainingHours -= delta

    return currentDate

def extracTime(sla):
    '''
        Esta función permite extraer el tiempo de un SLA
        Parameters:
            sla (str): SLA en formato de texto
        Returns:
            int: Tiempo extraído del SLA en horas
            habil (bool): Indica si el SLA es habilitado o no
    '''
    #Normalizamos el texto
    if not isinstance(sla, str):
        return sla, False
    
    sla = sla.strip().lower()
    
    # Extraemos el tiempo del SLA
    num = re.search(r'(\d+)\s*(hora|horas|día|dia|dias|días)', sla)
    if not num:
        return []
    
    unity = num.group(2)
    num = int(num.group(1))
    
    if 'hora' in unity:
        horas = num
    elif 'dia' in unity or 'día' in unity:
        horas = num * 24
    else:
        return []
    
    #Determinamos si es calendario
    if 'calendario' in sla:
        habil = False
    else:
        habil = True
        
    return [horas, habil]

if __name__ == "__main__":
    import locale
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para imprimir en español si está disponible

    fecha_inicial = dt.datetime.strptime('23/06/2025  12:12:45 PM', '%d/%m/%Y %I:%M:%S %p')
    intervalo_horas = '24 horas calendario'
    bank = 'banistmo'

    resultado = limitDate(fecha_inicial, intervalo_horas, bank)
    print("Fecha y hora hábil disponible:", resultado)