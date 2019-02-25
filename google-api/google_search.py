###################################################################
#Script Name    : google_search.py
# 
#
#Description    : A script to access the Google Search Console
#               : api, download analytcs info and dump to a CSV
#               : The resulting file can be loaded to Looker via the
#               : microservice google.googlesearch.json and will appear
#               : in the Looker project google_api
#
#Requirements   : Install python libraries: httplib2, oauth2client
#               : google-api-python-client
#               :
#               : You will need API credensials set up. If you don't have
#               : a project yet, follow these instructions. Otherwise,
#               : place your credentials.json file in the location defined 
#               : below.
#               :
#               : ------------------
#               : To set up the Google end of things, follow
#               :    https://developers.google.com/api-client-library/python/start/get_started
#               :
#               : Set up a Google account linked to an IDIR service account
#               : Create a new project at https://console.developers.google.com/projectcreate
#               :
#               : Enable the API via "+ Enable APIs and Services" by choosing:
#               :      "Google Search Console API"
#               :
#               : Click "Create Credentials" selecting:
#               :    Click on the small text to select that you want to create a "client id"
#               :    You will have to configure a consent screen. (document how you do this)
#               :    
#               :    After you submit, you will have to pick an application type. Choose Other
#               :    and choose something.
#               :    
#               :    Download the JSON file and place it in your directory as "credentials.json"
#               :    as describe by the variable below
#		:    
#		:    When you first run it, it will ask you do do an OAUTH validation, which 
#               :    will create a file credentials.dat, saving that auhtorization. 


import string
import re
from pprint import pprint
from datetime import date, timedelta, datetime
import httplib2
import json
import argparse
import apiclient.discovery
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
from apiclient.discovery import build

import sys # to read command line parameters
import os.path #file handling
from datetime import datetime
import io

outfile = "googlesearch-" + str(datetime.now().date()) + ".csv"

f = io.open(outfile, 'w', encoding='utf8')
start_dt = date(2018,11,1)
end_dt = date(2019,2,22)



API_NAME = 'searchconsole'
API_VERSION = 'v1'
DISCOVERY_URI = 'https://www.googleapis.com/discovery/v1/apis/webmasters/v3/rest'

parser = argparse.ArgumentParser(parents=[tools.argparser])
flags = parser.parse_args()
flags.noauth_local_webserver = True
credentials_file = 'credentials.json'

flow_scope='https://www.googleapis.com/auth/webmasters.readonly'
flow = flow_from_clientsecrets(credentials_file, scope= flow_scope, redirect_uri='urn:ietf:wg:oauth:2.0:oob')

flow.params['access_type'] = 'offline'
flow.params['approval_prompt'] = 'force'

storage = Storage('credentials.dat')
credentials = storage.get()

if credentials is not None and credentials.access_token_expired:
  try:
    credentials.refresh(h)
  except:
    pass

if credentials is None or credentials.invalid:
  credentials = tools.run_flow(flow, storage, flags)

http = credentials.authorize(httplib2.Http())

service = build(API_NAME, API_VERSION, http=http, discoveryServiceUrl=DISCOVERY_URI)
#site_list_response = service.sites().list().execute()
#pprint(site_list_response)

outrow = u"date|query|country|device|page|position|clicks|ctr|impressions\n"
f.write(outrow)

# Limit each query to 20000 rows. If there are more than 20000 rows in a given day, it will split the query up.
rowlimit = 20000
index = 0

def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)


for date in daterange(start_dt, end_dt):
	index = 0
	while (index == 0 or ('rows' in search_analytics_response)):
		print str(date)  + " " + str(index)
		bodyvar = {
			"aggregationType" : 'auto',
			"startDate": str(date),
			"endDate": str(date),
			"dimensions": [
				"date",
				"query",
				"country",
				"device",
				"page"
				],
			"rowLimit" : rowlimit,
       			"startRow" : index * rowlimit 
			}
		search_analytics_response = service.searchanalytics().query(siteUrl='https://www2.gov.bc.ca/', body=bodyvar).execute()
	#	pprint(search_analytics_response)
		index = index + 1
		if ('rows' in search_analytics_response):
			for row in search_analytics_response['rows']:
				outrow = ""
				for key in row['keys']:
					key = re.sub('\|', '', key) # for now, we strip | from searches
					key = re.sub('\\\\', '', key) # for now, we strip | from searches
					outrow = outrow + key + "|"
				outrow = outrow + str(row['position']) + "|" + re.sub('\.0','',str(row['clicks'])) + "|" + str(row['ctr']) + "|" + re.sub('\.0','',str(row['impressions'])) + "\n"
				f.write(outrow)
