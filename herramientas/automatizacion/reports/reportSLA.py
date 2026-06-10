import pandas as pd

from reports.reportCRQ import getReportCRQ
from reports.reportWO import getReportWO

def getReportSLA(initialDate, endDate, parameters, wo1, wo2):
    dataCRQ: pd.DataFrame = getReportCRQ(initialDate, endDate, parameters, True)['Datos CRQ']
    print('Datos CRQs procesados')
    dataWO: pd.DataFrame = getReportWO(wo1, wo2, parameters, True)['Datos WO']
    print('Datos WOs procesados')

    if dataCRQ.empty or dataWO.empty:
        raise ValueError('No se obtuvieron datos')
    
    return {
        'Datos CRQ': dataCRQ,
        'Datos WO': dataWO
    }    
    