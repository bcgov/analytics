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
#               : To set up the Google end of things, following this: 
#               :    https://developers.google.com/api-client-library/python/start/get_started
#               : the instructions are: 
#               :
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
#								:    
#								:    When you first run it, it will ask you do do an OAUTH validation, which 
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

import psycopg2 # For Amazon Redshift IO
import boto3    # For Amazon S3 IO

import sys # to read command line parameters
import os.path #file handling
import io # file and stream handling

# set up debugging
debug = True
def log(s):
    if debug:
        print s

# TODO: Replace file name hardcoding with env parameter
# Read configuration file
with open(os.environ['GOOGLE_MICROSERVICE_CONFIG']) as f:
  config = json.load(f)

sites = config['sites']
bucket = config['bucket']
dbtable = config['dbtable']

start_date_default = map(int, config['start_date_default'].split('-'))
start_date_default = date(start_date_default[0],start_date_default[1],start_date_default[2])

# set up the S3 resource
client = boto3.client('s3')
resource = boto3.resource('s3')

# set up the Redshift connection
conn_string = "dbname='snowplow' host='snowplow-ca-bc-gov-main-redshi-resredshiftcluster-13nmjtt8tcok7.c8s7belbz4fo.ca-central-1.redshift.amazonaws.com' port='5439' user='microservice' password=" + os.environ['pgpass']

for site in sites:
	# TODO: REPLACE WITH STREAM
	#f = io.open(outfile, 'w', encoding='utf8')
	stream = io.StringIO()

	# query the latest date for any search data on this site loaded to redshift
	con = psycopg2.connect(conn_string)
	cursor=con.cursor()
	query = "SELECT MAX(DATE) FROM google.googlesearch WHERE site = '{0}'".format(site)
	cursor.execute(query)

	last_loaded_date = (cursor.fetchall())[0][0]
	# The case where no data has yet been loaded for this site, start_dt will be the config set start date
	if last_loaded_date is None:
		start_dt = start_date_default
	else:
		# offset start_dt one day forward only if data already exists in redshift
		start_dt = last_loaded_date + timedelta(days=1)
	cursor.close()
	con.commit()
	con.close()

	# end_dt will be two days before the current date
	end_dt = (datetime.today() - timedelta(days=2)).date()

	# TODO if the end_dt is less than the start_dt, there's no more recent data to get; so go to next site
	if (end_dt - start_dt).days < 0:
		continue

	# set the file name that will be written to S3
	site_clean = re.sub(r'^https?:\/\/','', re.sub(r'\/$','',site))
	outfile = "googlesearch-" + site_clean + "-" + str(start_dt) + "-" + str(end_dt) + ".csv"
	object_key='client/google_gdx/{0}'.format(outfile)

	# calling the Google API
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

	# site is prepended to the response from the Google Search API
	outrow = u"site|date|query|country|device|page|position|clicks|ctr|impressions\n"
	stream.write(outrow)

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
			search_analytics_response = service.searchanalytics().query(siteUrl=site, body=bodyvar).execute()
		  # pprint(search_analytics_response)
			index = index + 1
			if ('rows' in search_analytics_response):
				for row in search_analytics_response['rows']:
					outrow = site + "|"
					for key in row['keys']:
						key = re.sub('\|', '', key) # for now, we strip | from searches
						key = re.sub('\\\\', '', key) # for now, we strip | from searches
						outrow = outrow + key + "|"
					outrow = outrow + str(row['position']) + "|" + re.sub('\.0','',str(row['clicks'])) + "|" + str(row['ctr']) + "|" + re.sub('\.0','',str(row['impressions'])) + "\n"
					stream.write(outrow)

	# write the stream to an outfile in the S3 bucket
	resource.Bucket(bucket).put_object(Key=object_key, Body=stream.getvalue())
	log('PUT_OBJECT: {0}:{1}'.format(outfile, bucket))
	object_summary = resource.ObjectSummary(bucket,object_key)
	log('OBJECT LOADED ON: {0} \nOBJECT SIZE: {1}'.format(object_summary.last_modified, object_summary.size))

	#TODO insert into redshift
	query = "copy " + dbtable +" FROM 's3://" + bucket + "/" + object_key + "' CREDENTIALS 'aws_access_key_id=" + os.environ['AWS_ACCESS_KEY_ID'] + ";aws_secret_access_key=" + os.environ['AWS_SECRET_ACCESS_KEY'] + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"
	logquery = "copy " + dbtable +" FROM 's3://" + bucket + "/" + object_key + "' CREDENTIALS 'aws_access_key_id=" + 'AWS_ACCESS_KEY_ID' + ";aws_secret_access_key=" + 'AWS_SECRET_ACCESS_KEY' + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"
	log(logquery)

	with psycopg2.connect(conn_string) as conn:
		with conn.cursor() as curs:
			try:
					curs.execute(query)
			except psycopg2.Error as e: # if the DB call fails, print error and place file in /bad
					log("Loading failed\n\n")
					log(e.pgerror)
			else:
					log("Loaded successfully\n\n")
