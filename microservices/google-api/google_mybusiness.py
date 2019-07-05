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
#               : Click "Create Credentials" selecting:
#               :   Click on the small text to select that you want to create
#               :   a "client id". You will have to configure a consent screen.
#               :   You must provide an Application name, and
#               :   under "Scopes for Google APIs" add the scopes:
#               :   "../auth/business.manage".
#               :
#               :   After you save, you will have to pick an application type.
#               :   Choose Other, and provide a name for this OAuth client ID.
#               :
#               :   Download the JSON file and place it in your working
#               :   directory as "credentials_mybusiness.json"
#               :
#               :   When you first run it, it will ask you do do an OAUTH
#               :   validation, which will create a file "mybusiness.dat",
#               :   saving that auhtorization.

import os
import sys
import json
import logging
import argparse
import httplib2

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
from apiclient.discovery import build

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
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# create file handler for logs at the INFO level
log_filename = '{0}'.format(os.path.basename(__file__).replace('.py', '.log'))
handler = logging.FileHandler(os.path.join('logs', log_filename), "a",
                              encoding=None, delay="true")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
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

bucket = config['bucket']
dbtable = config['dbtable']
locations = config['locations']


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


# Get the list of accounts the authenticated user has access to
# skipping the first one, since it describes the GDX Analytics personal account
accounts = service.accounts().list().execute()['accounts'][1:]

for loc in locations:
    for i in accounts:
        # validate match between account id and config file id
        if i["accountNumber"] == str(loc["id"]):
            account_uri = i["name"]

            # Get the list of locations under this account
            locationsList = service.accounts().locations().list(parent=account_uri).execute()
            # print(json.dumps(locationsList, indent=2) + "\n")

            # get an insights report for each location under the list of locations
            for i in locationsList["locations"]:
                location = i["name"]

                # # get the location and print its details
                # locationsGet = service.accounts().locations().get(name=location).execute()
                # print(json.dumps(locationsGet, indent=2) + "\n")

                # get the insights on this location and print
                reportInsights = service.accounts().locations().localPosts().reportInsights(name=location).execute()
                print(json.dumps(reportInsights, indent=2) + "\n")

                # ENDING EARLY WHILE TESTING
                sys.exit(1)
