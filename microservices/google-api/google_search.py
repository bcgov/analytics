###################################################################
#Script Name    : google_search.py
# 
#
#Description    : A script to access the Google Search Console
#               : api, download analytcs info and dump to a CSV in S3
#               : The resulting file is loaded to Redshift and then
#               : available to Looker through the project google_api.
#               : Calls span 30 days or less, and calls begin from
#               : the day after the latest data loaded into Redshift,
#               : or 16 months ago, or on the date specified in the
#               : file referenced by the GOOGLE_MICROSERVICE_CONFIG
#               : environment variable. The config JSONschema is
#               : defined in the google-api README.md file.
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
#               :    You will have to configure a consent screen.
#               :    You must provide an Application name, and under "Scopes for Google APIs"
#               :    add the scopes: "../auth/webmasters" and "../auth/webmasters.readonly".
#               :    
#               :    After you save, you will have to pick an application type. Choose Other
#               :    and provide a name for this OAuth client ID.
#               :    
#               :    Download the JSON file and place it in your directory as "credentials.json"
#               :    as describe by the variable below
#               :    
#               :    When you first run it, it will ask you do do an OAUTH validation, which 
#               :    will create a file "credentials.dat", saving that auhtorization. 


import string
import re
from pprint import pprint
from datetime import date, timedelta, datetime
from time import sleep
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

def last_loaded(site_name):
    # Check for a last loaded date in Redshift
    # Load the Redshift connection
    con = psycopg2.connect(conn_string)
    cursor=con.cursor()
    #query the latest date for any search data on this site loaded to redshift
    query = "SELECT MAX(DATE) FROM google.googlesearch WHERE site = '{0}'".format(site_name)
    cursor.execute(query)
    # get the last loaded date
    last_loaded_date = (cursor.fetchall())[0][0]
    # close the redshift connection
    cursor.close()
    con.commit()
    con.close()
    return last_loaded_date

# the latest available Google API data is two less less today
latest_date = date.today() - timedelta(days=2)

# Read configuration file from env parameter
with open(os.environ['GOOGLE_MICROSERVICE_CONFIG']) as f:
  config = json.load(f)

sites = config['sites']
bucket = config['bucket']
dbtable = config['dbtable']

# set up the S3 resource
client = boto3.client('s3')
resource = boto3.resource('s3')

# set up the Redshift connection
conn_string = "dbname='snowplow' host='snowplow-ca-bc-gov-main-redshi-resredshiftcluster-13nmjtt8tcok7.c8s7belbz4fo.ca-central-1.redshift.amazonaws.com' port='5439' user='microservice' password=" + os.environ['pgpass']

for site_item in sites:
    # read the config item for the site name and default start date if specified
    site_name = site_item["name"]

    # get the last loaded date (which may be None if this site has not previously been loaded into Redshift)
    last_loaded_date = last_loaded(site_name)

    # if the last load is 2 days old, there will be no new data in Google to grab for this site
    if last_loaded_date is not None and last_loaded_date >= latest_date:
        continue

    # The default start date for queries will be the optional one set in the JSON config
    start_date_default = site_item.get("start_date_default")
    # if no start date is specified, set it to 16 months ago
    if start_date_default is None:
        start_date_default = date.today() - timedelta(days=480)
    # if a start date was specified, it has to be formatted into a date type
    else:
        start_date_default = map(int, start_date_default.split('-'))
        start_date_default = date(start_date_default[0],start_date_default[1],start_date_default[2])

    # Load 30 days at a time until the data in Redshift has caught up to the most recently available data from Google
    while (last_loaded_date is not latest_date):

        last_loaded_date = last_loaded(site_name)

        # if there isn't data in Redshift for this site, start at the start_date_default set earlier
        if last_loaded_date is None:
            start_dt = start_date_default
        else:
            start_dt = last_loaded_date + timedelta(days=1) # offset start_dt one day ahead of last Redshift-loaded data
        
        # end_dt will be up to 1 month ahead of start_dt, or up to two days before now, whichever is less.
        end_dt = min(start_dt + timedelta(days=30), latest_date)

        # set the file name that will be written to S3
        site_clean = re.sub(r'^https?:\/\/','', re.sub(r'\/$','',site_name))
        outfile = "googlesearch-" + site_clean + "-" + str(start_dt) + "-" + str(end_dt) + ".csv"
        object_key='client/google_gdx/{0}'.format(outfile)

        # calling the Google API. If credentials.dat is not yet generated, Google Account validation will be necessary
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

        # prepare stream
        stream = io.StringIO()

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
            # A wait time of 250ms each query reduces HTTP 429 error "Rate Limit Exceeded", handled below
            wait_time = 0.25
            sleep(wait_time)
            
            index = 0
            while (index == 0 or ('rows' in search_analytics_response)):
                print str(date)  + " " + str(index)
                
                # The request body for the Google Search API query
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

                # This query to the Google Search API may eventually yield an HTTP response code of 429, "Rate Limit Exceeded".
                # The handling attempt below will increase the wait time on each re-attempt up to 10 times.
                # As a scheduled job, ths microservice will restart after the last successful load to Redshift.
                retry = 1
                while True:
                    try:
                        search_analytics_response = service.searchanalytics().query(siteUrl=site_name, body=bodyvar).execute()
                    except:
                        if retry == 11:
                            print "Failing with HTTP error after 10 retries with query time easening."
                            sys.exit()
                        wait_time = wait_time * 2
                        print "retryring {0} with wait time {1}".format(retry,wait_time)
                        retry = retry + 1
                        sleep(wait_time)
                    else:
                        break
                
                index = index + 1
                if ('rows' in search_analytics_response):
                    for row in search_analytics_response['rows']:
                        outrow = site_name + "|"
                        for key in row['keys']:
                            key = re.sub('\|', '', key) # for now, we strip | from searches
                            key = re.sub('\\\\', '', key) # for now, we strip | from searches
                            outrow = outrow + key + "|"
                        outrow = outrow + str(row['position']) + "|" + re.sub('\.0','',str(row['clicks'])) + "|" + str(row['ctr']) + "|" + re.sub('\.0','',str(row['impressions'])) + "\n"
                        stream.write(outrow)

        # Write the stream to an outfile in the S3 bucket with naming like "googlesearch-sitename-startdate-enddate.csv"
        resource.Bucket(bucket).put_object(Key=object_key, Body=stream.getvalue())
        log('PUT_OBJECT: {0}:{1}'.format(outfile, bucket))
        object_summary = resource.ObjectSummary(bucket,object_key)
        log('OBJECT LOADED ON: {0} \nOBJECT SIZE: {1}'.format(object_summary.last_modified, object_summary.size))

        # Prepare the Redshift query
        query = "copy " + dbtable +" FROM 's3://" + bucket + "/" + object_key + "' CREDENTIALS 'aws_access_key_id=" + os.environ['AWS_ACCESS_KEY_ID'] + ";aws_secret_access_key=" + os.environ['AWS_SECRET_ACCESS_KEY'] + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"
        logquery = "copy " + dbtable +" FROM 's3://" + bucket + "/" + object_key + "' CREDENTIALS 'aws_access_key_id=" + 'AWS_ACCESS_KEY_ID' + ";aws_secret_access_key=" + 'AWS_SECRET_ACCESS_KEY' + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"
        log(logquery)

        # Load into Redshift
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as curs:
                try:
                    curs.execute(query)
                except psycopg2.Error as e: # if the DB call fails, print error and place file in /bad
                    log("Loading failed\n\n")
                    log(e.pgerror)
                else:
                    log("Loaded successfully\n\n")
