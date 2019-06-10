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
#               :   "../auth/webmasters" and "../auth/webmasters.readonly".
#               :
#               :   After you save, you will have to pick an application type.
#               :   Choose Other, and provide a name for this OAuth client ID.
#               :
#               :   Download the JSON file and place it in your directory as
#               :   "credentials.json" as described by the variable below
#               :
#               :   When you first run it, it will ask you do do an OAUTH
#               :   validation, which will create a file "credentials.dat",
#               :   saving that auhtorization.


import re
from datetime import date, timedelta
from time import sleep
import httplib2
import json
import argparse
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import tools
from apiclient.discovery import build
import psycopg2  # For Amazon Redshift IO
import boto3     # For Amazon S3 IO
import sys       # to read command line parameters
import os.path   # file handling
import io        # file and stream handling

# Set time zone
# os.environ['TZ'] = 'Americas/Vancouver'

# set up logging
import logging
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

# calling the Google API. If credentials.dat is not yet generated, Google Account validation will be necessary
API_NAME = 'mybusiness'
API_VERSION = 'v4'
DISCOVERY_URI = 'https://developers.google.com/my-business/samples/mybusiness_google_rest_v4.json'

parser = argparse.ArgumentParser(parents=[tools.argparser])
flags = parser.parse_args()
flags.noauth_local_webserver = True
credentials_file = 'credentials.json'

flow_scope = 'https://www.googleapis.com/auth/plus.business.manage'
flow = flow_from_clientsecrets(credentials_file, scope= flow_scope, redirect_uri='urn:ietf:wg:oauth:2.0:oob')

flow.params['access_type'] = 'offline'
flow.params['approval_prompt'] = 'force'

storage = Storage('credentials.dat')
credentials = storage.get()

if credentials is not None and credentials.access_token_expired:
    try:
        h = httplib2.Http()
        credentials.refresh(h)
    except Exception:
        pass

if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, flags)

http = credentials.authorize(httplib2.Http())

service = build(API_NAME, API_VERSION, http=http, discoveryServiceUrl=DISCOVERY_URI)
# site_list_response = service.sites().list().execute()

# prepare stream
stream = io.StringIO()

# Limit each query to 20000 rows. If there are more than 20000 rows in a given day, it will split the query up.
rowlimit = 20000
index = 0

start_dt = date("2019","6","1")
end_dt = date("2019","6","4")

def daterange(date1, date2):
    for n in range(int((date2 - date1).days)+1):
        yield date1 + timedelta(n)

mybusiness_analytics_response= ''

for date_in_range in daterange(start_dt, end_dt):
    # A wait time of 250ms each query reduces HTTP 429 error
    # "Rate Limit Exceeded", handled below
    wait_time = 0.25
    sleep(wait_time)

    index = 0
    while (index == 0 or ('rows' in mybusiness_analytics_response)):
        logger.debug(str(date_in_range) + " " + str(index))

        # The request body for the Google My Business API query
        bodyvar = {
            "aggregationType": 'auto',
            "startDate": str(date_in_range),
            "endDate": str(date_in_range),
            "dimensions": [
                "date",
                "query",
                "country",
                "device",
                "page"
                ],
            "rowLimit": rowlimit,
            "startRow": index * rowlimit
            }

        # This query to the Google My Business API may eventually yield an
        # HTTP response code of 429, "Rate Limit Exceeded".
        # The handling attempt below will increase the wait time on
        # each re-attempt up to 10 times.

        # As a scheduled job, ths microservice will restart after the
        # last successful load to Redshift.
        retry = 1
        while True:
            try:
                mybusiness_analytics_response = service.searchanalytics().query(siteUrl=site_name, body=bodyvar).execute()
            except Exception as e:
                if retry == 11:
                    logger.error("Failing with HTTP error after 10 retries with query time easening.")
                    sys.exit()
                wait_time = wait_time * 2
                logger.warning("retryring {0} with wait time {1}"
                               .format(retry, wait_time))
                retry = retry + 1
                sleep(wait_time)
            else:
                break

        index = index + 1
        if ('rows' in mybusiness_analytics_response):
            for row in mybusiness_analytics_response['rows']:
                outrow = site_name + "|"
                for key in row['keys']:
                    # for now, we strip | from searches
                    key = re.sub('\|', '', key)
                    # for now, we strip | from searches
                    key = re.sub('\\\\', '', key)
                    outrow = outrow + key + "|"
                outrow = outrow + str(row['position']) + "|" + re.sub('\.0', '', str(row['clicks'])) + "|" + str(row['ctr']) + "|" + re.sub('\.0', '', str(row['impressions'])) + "\n"
                stream.write(outrow)

# Write the stream to an outfile in the S3 bucket with naming
# like "google_mybusiness-sitename-startdate-enddate.csv"
resource.Bucket(bucket).put_object(Key=object_key,
                                   Body=stream.getvalue())
logger.debug('PUT_OBJECT: {0}:{1}'.format(outfile, bucket))
object_summary = resource.ObjectSummary(bucket, object_key)
logger.debug('OBJECT LOADED ON: {0} \nOBJECT SIZE: {1}'
             .format(object_summary.last_modified,
                     object_summary.size))

# Prepare the Redshift query
query = "copy " + dbtable + " FROM 's3://" + bucket + "/" + object_key + "' CREDENTIALS 'aws_access_key_id=" + os.environ['AWS_ACCESS_KEY_ID'] + ";aws_secret_access_key=" + os.environ['AWS_SECRET_ACCESS_KEY'] + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"
logquery = "copy " + dbtable + " FROM 's3://" + bucket + "/" + object_key + "' CREDENTIALS 'aws_access_key_id=" + 'AWS_ACCESS_KEY_ID' + ";aws_secret_access_key=" + 'AWS_SECRET_ACCESS_KEY' + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"
logger.debug(logquery)

# Load into Redshift
with psycopg2.connect(conn_string) as conn:
    with conn.cursor() as curs:
        try:
            curs.execute(query)
        # if the DB call fails, print error and place file in /bad
        except psycopg2.Error as e:
            logger.error("Loading failed {0} index {1} for {2} with error:\n{3}".format(site_name, index, date_in_range, e.pgerror))
        else:
            logger.info("Loaded {0} index {1} for {2} successfully"
                        .format(site_name, index, date_in_range))
# if we didn't add any new rows, set last_loaded_date to latest_date to
# break the loop, otherwise, set it to the last loaded date
if last_loaded_date == last_loaded(site_name):
    last_loaded_date = latest_date
else:
    # refresh last_loaded with the most recent load date
    last_loaded_date = last_loaded(site_name)


# now we run the single-time load on the cmslite.google_pdt
query = """
-- perform this as a transaction.
-- Either the whole query completes, or it leaves the old table intact
BEGIN;
DROP TABLE IF EXISTS cmslite.google_pdt_scratch;
DROP TABLE IF EXISTS cmslite.google_pdt_old;

CREATE TABLE IF NOT EXISTS cmslite.google_pdt_scratch (
        "site"          VARCHAR(255),
        "date"          date,
        "query"         VARCHAR(2047),
        "country"       VARCHAR(255),
        "device"        VARCHAR(255),
        "page"          VARCHAR(2047),
        "position"      FLOAT,
        "clicks"        DECIMAL,
        "ctr"           FLOAT,
        "impressions"   DECIMAL,
        "node_id"       VARCHAR(255),
        "page_urlhost"  VARCHAR(255),
        "title"         VARCHAR(2047),
        "theme_id"      VARCHAR(255),
        "subtheme_id"   VARCHAR(255),
        "topic_id"      VARCHAR(255),
        "theme"         VARCHAR(2047),
        "subtheme"      VARCHAR(2047),
        "topic"         VARCHAR(2047)
);
ALTER TABLE cmslite.google_pdt_scratch OWNER TO microservice;
GRANT SELECT ON cmslite.google_pdt_scratch TO looker;

INSERT INTO cmslite.google_pdt_scratch
      SELECT gs.*,
      COALESCE(node_id,'') AS node_id,
      SPLIT_PART(site, '/',3) as page_urlhost,
      title,
      theme_id, subtheme_id, topic_id, theme, subtheme, topic
      FROM google.google_mybusiness AS gs
      -- fix for misreporting of redirected front page URL in Google My Business
      LEFT JOIN cmslite.themes AS themes ON CASE WHEN page = 'https://www2.gov.bc.ca/' THEN 'https://www2.gov.bc.ca/gov/content/home' ELSE page END = themes.hr_url;

ALTER TABLE cmslite.google_pdt RENAME TO google_pdt_old;
ALTER TABLE cmslite.google_pdt_scratch RENAME TO google_pdt;
DROP TABLE cmslite.google_pdt_old;
COMMIT;
"""

logger.debug(query)
with psycopg2.connect(conn_string) as conn:
    with conn.cursor() as curs:
        try:
            curs.execute(query)
        except psycopg2.Error as e:
            logger.error("Google My Business PDT loading failed\n{0}".
                         format(e.pgerror))
        else:
            logger.info("Google My Business PDT loaded successfully")
