import sys
import datetime
sys.path.insert(0, 'automatizacion_portable')
from reports.func.queryDataApi import queryData
import os
from dotenv import load_dotenv
load_dotenv()

initialDate='2026-05-31'
endDate='2026-06-08'
urlOpenIncidents = (
    f"{os.getenv('URLINC')}"
    f"fields=values(Incident Number,Service Type,TicketType,Priority,Original Incident Number,Status, SLM Status, Submit Date,Last Resolved Date,Assignee,Full Name,HPD_CI,Description,Assigned Group,Company)"
    f"&q= 'Submit Date' >= \"{initialDate}\" and 'Submit Date' <= \"{endDate}\" and ('Status' = \"Assigned\" or 'Status' = \"Pending\" or 'Status' = \"In Progress\")"
)
urlBCO = f"{os.getenv('URLBCO')}fields=values(Support Group Name,Support Organization)"
print('urlOpenIncidents:', urlOpenIncidents)
print('urlBCO:', urlBCO)
openIncidentData = queryData(urlOpenIncidents)
bcoData = queryData(urlBCO)
print('openIncidentData len:', len(openIncidentData))
print('bcoData len:', len(bcoData))
