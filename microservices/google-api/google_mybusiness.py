###################################################################
# Script Name   : google_mybusiness.py
#
#
# Description   : A script to access the Google Locations/My Business
#               : api, download analytcs info and dump to a CSV in S3
#               : The resulting file is loaded to Redshift and then
#               : available to Looker through the project google_api.
#
# Requirements  : Install python libraries: httplib2, oauth2client
#               : google-api-python-client
#               :
#               : You will need API credensials set up. If you don't have
#               : a project yet, follow these instructions. Otherwise,
#               : place your credentials.json file in the location defined
#               : below.
#               :
#               : ------------------
#               : To set up the Google end of things, following this:
#   : https://developers.google.com/api-client-library/python/start/get_started
#               : the instructions are:
#               :
#               :
#               : Set up a Google account linked to an IDIR service account
#               : Create a new project at
#               : https://console.developers.google.com/projectcreate
#               :
#               : Click 'Create Credentials' selecting:
#               :   Click on the small text to select that you want to create
#               :   a 'client id'. You will have to configure a consent screen.
#               :   You must provide an Application name, and
#               :   under 'Scopes for Google APIs' add the scopes:
#               :   '../auth/business.manage'.
#               :
#               :   After you save, you will have to pick an application type.
#               :   Choose Other, and provide a name for this OAuth client ID.
#               :
#               :   Download the JSON file and place it in your working
#               :   directory as 'credentials_mybusiness.json'
#               :
#               :   When you first run it, it will ask you do do an OAUTH
#               :   validation, which will create a file 'mybusiness.dat',
#               :   saving that auhtorization.

import os
import sys
import json
import boto3
import logging
import psycopg2
import argparse
import httplib2
import pandas as pd
import dateutil.relativedelta

from io import BytesIO
import datetime
from datetime import timedelta
from apiclient.discovery import build
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets


# Ctrl+C
def signal_handler(signal, frame):
    logger.debug('Ctrl+C pressed!')
    sys.exit(0)


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler for logs at the WARNING level
# This will be emailed when the cron task runs; formatted to give messages only
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# create file handler for logs at the INFO level
log_filename = '{0}'.format(os.path.basename(__file__).replace('.py', '.log'))
handler = logging.FileHandler(os.path.join('logs', log_filename), 'a',
                              encoding=None, delay='true')
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s:%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Command line arguments
parser = argparse.ArgumentParser(
    parents=[tools.argparser],
    description='GDX Analytics ETL utility for Google My Business insights.')
parser.add_argument('-o', '--cred', help='OAuth Credentials JSON file.')
parser.add_argument('-a', '--auth', help='Stored authorization dat file')
parser.add_argument('-c', '--conf', help='Microservice configuration file.',)
parser.add_argument('-d', '--debug', help='Run in debug mode.',
                    action='store_true')
flags = parser.parse_args()

CLIENT_SECRET = flags.cred
AUTHORIZATION = flags.auth
CONFIG = flags.conf


# Parse the CONFIG file as a json object and load its elements as variables
with open(CONFIG) as f:
    config = json.load(f)

config_bucket = config['bucket']
config_dbtable = config['dbtable']
config_metrics = config['metrics']
config_locations = config['locations']


# set up the S3 resource
client = boto3.client('s3')
resource = boto3.resource('s3')


# set up the Redshift connection
conn_string = ("dbname='snowplow' "
               "host='snowplow-ca-bc-gov-main-redshi-resredshiftcluster-"
               "13nmjtt8tcok7.c8s7belbz4fo.ca-central-1.redshift.amazonaws.com"
               "' port='5439' user='microservice' password="
               + os.environ['pgpass'])


# Setup OAuth 2.0 flow for the Google My Business API
API_NAME = 'mybusiness'
API_VERSION = 'v4'
DISCOVERY_URI = 'https://developers.google.com/my-business/samples/\
{api}_google_rest_{apiVersion}.json'


# Google API Access requires a browser-based authentication step to create
# the stored authorization .dat file. Forcign noauth_local_webserver to True
# allows for authentication from an environment without a browser, such as EC2.
flags.noauth_local_webserver = True


# Initialize the OAuth2 authorization flow.
# The string urn:ietf:wg:oauth:2.0:oob is for non-web-based applications.
# The prompt='consent' Retrieves the refresh token.
flow_scope = 'https://www.googleapis.com/auth/business.manage'
flow = flow_from_clientsecrets(CLIENT_SECRET, scope=flow_scope,
                               redirect_uri='urn:ietf:wg:oauth:2.0:oob',
                               prompt='consent')


# Specify the storage path for the .dat authentication file
storage = Storage(AUTHORIZATION)
credentials = storage.get()

# Refresh the access token if it expired
if credentials is not None and credentials.access_token_expired:
    try:
        h = httplib2.Http()
        credentials.refresh(h)
    except Exception:
        pass

# Acquire credentials in a command-line application
if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, flags)

# Apply credential headers to all requests made by an httplib2.Http instance
http = credentials.authorize(httplib2.Http())

# Build the service object
service = build(
    API_NAME, API_VERSION, http=http, discoveryServiceUrl=DISCOVERY_URI)
# site_list_response = service.sites().list().execute()


# Check for a last loaded date in Redshift
# Load the Redshift connection
def last_loaded(dbtable, location_id):
    con = psycopg2.connect(conn_string)
    cursor = con.cursor()
    # query the latest date for any search data on this site loaded to redshift
    query = ("SELECT MAX(Date) "
             "FROM {0} "
             "WHERE location_id = '{1}'").format(dbtable, location_id)
    cursor.execute(query)
    # get the last loaded date
    last_loaded_date = (cursor.fetchall())[0][0]
    # close the redshift connection
    cursor.close()
    con.commit()
    con.close()
    return last_loaded_date


# Location Check

# Get the list of accounts that the Google account being used to access
# the My Business API has rights to read location insights from
# (ignoring the first one, since it is the 'self' reference account).
accounts = service.accounts().list().execute()['accounts'][1:]

# check that all locations defined in the configuration file are available
# to the authencitad account being used to access the MyBusiness API, and
# append those accounts information into a 'validated_locations' list.
validated_accounts = []
for loc in config_locations:
    try:
        validated_accounts.append(
            next({
                'uri': item['name'],
                'name': item['accountName'],
                'id': item['accountNumber'],
                'client_shortname': loc['client_shortname'],
                'start_date': loc['start_date'],
                'end_date': loc['end_date'],
                'names_replacement': loc['names_replacement']}
                 for item
                 in accounts
                 if item['accountNumber'] == str(loc['id'])))
    except StopIteration:
        logger.warning(
            'No API access to {0}. Excluding from insights query.'
            .format(loc['name']))
        continue

# iterate over ever location of every account
for account in validated_accounts:

    dbtable = config_dbtable
    # Create a dataframe with dates as rows and columns according to the table
    df = pd.DataFrame()
    account_uri = account['uri']
    locations = (
        service.accounts().locations().list(parent=account_uri).execute())
    # we will handle each location separately
    for loc in locations['locations']:
        # substring replacement for location names from config file
        find_in_name = account['names_replacement'][0]
        rep_in_name = account['names_replacement'][1]

        # encode as ASCII for dataframe
        location_uri = loc['name'].encode('ascii', 'ignore')
        location_name = loc['locationName'].replace(find_in_name, rep_in_name)

        # if a start_date is defined in the config file, use that date
        start_date = account['start_date']
        if start_date == '':
            # The earliest available data is from 18 months ago from the
            # query day. Adding a day accounts for possible timezone offset.
            # timedelta does not support months, dateutil.relativedelta does.
            # reference: https://stackoverflow.com/a/14459459/5431461
            start_date = (
                datetime.datetime.today().date()
                - dateutil.relativedelta.relativedelta(months=18)
                + timedelta(days=1)
                ).isoformat()

        # query RedShift to see if there is a date already loaded
        last_loaded_date = last_loaded(config_dbtable, loc['name'])
        if last_loaded_date is not None:
            logger.info("first time loading {}".format(account['name']))

        # If it is loaded with some data for this ID, use that date plus
        # one day as the start_date.
        if (last_loaded_date is not None
                and last_loaded_date.isoformat() >= start_date):
            start_date = last_loaded_date + timedelta(days=1)
            start_date = start_date.isoformat()

        start_time = start_date + 'T00:00:00Z'

        # if an end_date is defined in the config file, use that date
        end_date = account['end_date']
        if end_date == '':
            # The most recent data available is from two days ago
            end_date = (
                datetime.datetime.today().date() - timedelta(days=2)
                ).isoformat()

        end_time = end_date + 'T00:00:00Z'

        # if start and end times are same, then there's no new data
        if start_time == end_time:
            logger.info("Redshift already contains the latest avaialble data.")
            continue

        # the API call must construct each metric request in a list of dicts
        metricRequests = []
        for metric in config_metrics:
            metricRequests.append(
                {
                    'metric': metric,
                    'options': 'AGGREGATED_DAILY'
                    }
                )

        bodyvar = {
            'locationNames': ['{0}'.format(location_uri)],
            'basicRequest': {
                # https://developers.google.com/my-business/reference/rest/v4/Metric
                'metricRequests': metricRequests,
                # https://developers.google.com/my-business/reference/rest/v4/BasicMetricsRequest
                # The maximum range is 18 months from the request date.
                'timeRange': {
                    'startTime': '{0}'.format(start_time),
                    'endTime': '{0}'.format(end_time)
                    }
                }
            }

        # retrieves the request for this location.
        reportInsights = \
            service.accounts().locations().\
            reportInsights(body=bodyvar, name=account_uri).execute()

        # (json.dumps(reportInsights, indent=2) + '\n')

        # We constrain API calls to one location at a time, so
        # there is only one element in the locationMetrics list:
        metrics = reportInsights['locationMetrics'][0]['metricValues']

        for metric in metrics:
            metric_name = metric['metric'].lower().encode('ascii', 'ignore')
            # iterate on the dimensional values for this metric.

            dimVals = metric['dimensionalValues']
            for results in dimVals:
                # just get the YYYY-MM-DD day; dropping the T07:00:00Z
                day = results['timeDimension']['timeRange']['startTime'][:10]
                client = account['client_shortname']
                value = results['value'] if 'value' in results else 0
                row = pd.DataFrame([{'date': day,
                                     'client': client,
                                     'location': location_name,
                                     'location_id': location_uri,
                                     metric_name: int(value)}])
                # Since we are growing both rows and columns, we must concat
                # the dataframe with the new row. This will create NaN values.
                df = pd.concat([df, row], sort=False)

        # sort the dataframe by date
        df.sort_values('date')

        # collapse rows on the groupers columns, which will remove all NaNs.
        # reference: https://stackoverflow.com/a/36746793/5431461
        groupers = ['date', 'client', 'location', 'location_id']
        groupees = [e.lower() for e in config_metrics]
        df = df.groupby(groupers).apply(lambda g: g[groupees].ffill().iloc[-1])

        # an artifact of the NaNs is that dtypes are float64.
        # These can be downcast to integers, as there is no need for a decimal.
        df = df.astype('int64')

        # prepare csv buffer
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=True, header=True, sep='|')

        # Set up the S3 path to write the csv buffer to
        object_key_path = 'client/google_mybusiness_{}/'.format(
            account['client_shortname'])

        outfile = 'gmb_{0}_{1}_{2}.csv'.format(
            location_name.replace(' ', '-'),
            start_date,
            end_date)
        object_key = object_key_path + outfile

        resource.Bucket(config_bucket).put_object(
            Key=object_key,
            Body=csv_buffer.getvalue())
        logger.debug('PUT_OBJECT: {0}:{1}'.format(outfile, config_bucket))
        object_summary = resource.ObjectSummary(config_bucket, object_key)
        logger.debug('OBJECT LOADED ON: {0} \nOBJECT SIZE: {1}'
                     .format(object_summary.last_modified,
                             object_summary.size))

        # Prepare the Redshift COPY command.
        query = (
            "copy " + config_dbtable + " FROM 's3://" + config_bucket
            + "/" + object_key + "' CREDENTIALS 'aws_access_key_id="
            + os.environ['AWS_ACCESS_KEY_ID'] + ";aws_secret_access_key="
            + os.environ['AWS_SECRET_ACCESS_KEY']
            + ("' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER"
                + " '|' NULL AS '-' ESCAPE;"))
        logquery = (
            "copy " + config_dbtable + " FROM 's3://" + config_bucket
            + "/" + object_key + "' CREDENTIALS 'aws_access_key_id="
            + 'AWS_ACCESS_KEY_ID' + ";aws_secret_access_key="
            + 'AWS_SECRET_ACCESS_KEY' + (
                "' IGNOREHEADER AS 1 MAXERROR"
                + " AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"))
        logger.debug(logquery)

        # Connect to Redshift and execute the query.
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as curs:
                try:
                    curs.execute(query)
                except psycopg2.Error as e:
                    logger.error("".join((
                        "Loading failed {0} with error:\n{1}"
                        .format(location_name, e.pgerror),
                        " Object key: {0}".format(object_key.split('/')[-1]))))
                else:
                    logger.info("".join((
                        "Loaded {0} successfully."
                        .format(location_name),
                        ' Object key: {0}'.format(object_key.split('/')[-1]))))

        # END EARLY WHILE TESTING
        sys.exit(1)
