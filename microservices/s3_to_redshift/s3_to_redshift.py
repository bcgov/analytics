###################################################################
# Script Name   : s3_to_redshift.py
#
# Description   : Microservice script to load a csv file from s3
#               : and load it into Redshift
#
# Requirements  : You must set the following environment variables
#               : to establish credentials for the microservice user
#
#               : export AWS_ACCESS_KEY_ID=<<KEY>>
#               : export AWS_SECRET_ACCESS_KEY=<<SECRET_KEY>>
#               : export pgpass=<<DB_PASSWD>>
#
#
# Usage         : python s3_to_redshift.py configfile.json
#

import boto3  # s3 access
import pandas as pd  # data processing
import re  # regular expressions
from io import StringIO
from io import BytesIO
import os  # to read environment variables
import psycopg2  # to connect to Redshift
import json  # to read json config files
import sys  # to read command line parameters
import os.path  # file handling

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

# Read configuration file
if (len(sys.argv) != 2):  # will be 1 if no arguments, 2 if one argument
    print "Usage: python s3_to_redshift.py config.json"
    sys.exit(1)
configfile = sys.argv[1]
if os.path.isfile(configfile) is False:  # confirm that the file exists
    print "Invalid file name " + configfile
    sys.exit(1)
with open(configfile) as f:
    data = json.load(f)

# Set up variables from config file
bucket = data['bucket']
source = data['source']
destination = data['destination']
directory = data['directory']
doc = data['doc']
if 'dbschema' in data:
    dbschema = data['dbschema']
else:
    dbschema = 'microservice'
dbtable = data['dbtable']
table_name = dbtable[dbtable.rfind(".")+1:]
column_count = data['column_count']
columns = data['columns']
dtype_dic = {}
if 'dtype_dic_strings' in data:
    for fieldname in data['dtype_dic_strings']:
        dtype_dic[fieldname] = str
delim = data['delim']
truncate = data['truncate']
if 'drop_columns' in data:
    drop_columns = data['drop_columns']
else:
    drop_columns = {}

# set up S3 connection
client = boto3.client('s3')  # low-level functional API
resource = boto3.resource('s3')  # high-level object-oriented API
my_bucket = resource.Bucket(bucket)  # subsitute this for your s3 bucket name.
b_name = my_bucket.name

# Database connection string
conn_string = "dbname='snowplow' host='snowplow-ca-bc-gov-main-redshi-resredsh\
iftcluster-13nmjtt8tcok7.c8s7belbz4fo.ca-central-1.redshift.amazonaws.com' \
port='5439' user='microservice' password=" + os.environ['pgpass']


# Constructs the database copy query string
def copy_query(dbtable, batchfile, log):
    if log:
        aws_key = 'AWS_ACCESS_KEY_ID'
        aws_secret_key = 'AWS_SECRET_ACCESS_KEY'
    else:
        aws_key = os.environ['AWS_ACCESS_KEY_ID']
        aws_secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
    query = """
COPY {0}\nFROM 's3://{1}/{2}'\n\
CREDENTIALS 'aws_access_key_id={3};aws_secret_access_key={4}'\n\
IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;\n
""".format(dbtable, b_name, batchfile, aws_key, aws_secret_key)
    return query


for object_summary in my_bucket.objects.filter(Prefix=source + "/"
                                               + directory + "/"):
    if re.search(doc + '$', object_summary.key):
        logger.debug('{0}:{1}'.format(b_name, object_summary.key))

        # Check to see if the file has been processed already
        batchfile = destination + "/batch/" + object_summary.key
        goodfile = destination + "/good/" + object_summary.key
        badfile = destination + "/bad/" + object_summary.key
        try:
            client.head_object(Bucket=bucket, Key=goodfile)
        except Exception as e:
            True
        else:
            logger.debug("File processed already. Skip.")
            continue
        try:
            client.head_object(Bucket=bucket, Key=badfile)
        except Exception as e:
            True
        else:
            logger.debug("File failed already. Skip.")
            continue
        logger.debug("File not already processed. Proceed.")

        obj = client.get_object(Bucket=bucket, Key=object_summary.key)
        body = obj['Body']
        # Check that the file decodes as UTF-8. If it fails move to bad and end
        try:
            csv_string = body.read().decode('utf-8')
        except UnicodeDecodeError as e:
            logger.error(''.join((
                          "Decoding UTF-8 failed for file {0}\n{1}"
                          .format(object_summary.key, e.message),
                          "Keying to badfile and skipping.")))
            try:
                client.copy_object(
                    Bucket="sp-ca-bc-gov-131565110619-12-microservices",
                    CopySource="sp-ca-bc-gov-131565110619-12-microservices/"
                    + object_summary.key, Key=badfile)
            except Exception as e:
                logger.exception("S3 transfer failed.\n{0}".format(e.message))
            continue

        # Check for an empty file. If it's empty, accept it as good and move on
        try:
            df = pd.read_csv(StringIO(csv_string), sep=delim, index_col=False,
                             dtype=dtype_dic, usecols=range(column_count))
        except Exception as e:
            logger.exception('exption reading {0}'.format(object_summary.key))
            if (str(e) == "No columns to parse from file"):
                logger.warning('File is empty, keying to goodfile \
                               and proceeding.')
                outfile = goodfile
            else:
                logger.warning('File not empty, keying to badfile \
                               and proceeding.')
                outfile = badfile
            client.copy_object(Bucket="sp-ca-bc-gov-131565110619-12-\
                               microservices", CopySource="sp-ca-bc-gov-\
                               131565110619-12-microservices/"
                               + object_summary.key, Key=outfile)
            continue

        df.columns = columns

        if 'drop_columns' in data:  # Drop any columns marked for dropping
            df = df.drop(columns=drop_columns)

        # Run replace on some fields to clean the data up
        if 'replace' in data:
            for thisfield in data['replace']:
                df[thisfield['field']].replace(
                    thisfield['old'], thisfield['new'])

        # Clean up date fields
        # for each field listed in the dateformat
        # array named "field" apply "format"
        if 'dateformat' in data:
            for thisfield in data['dateformat']:
                df[thisfield['field']] = \
                    pd.to_datetime(df[thisfield['field']],
                                   format=thisfield['format'])

        # Put the full data set into a buffer and write it
        # to a "|" delimited file in the batch directory
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, header=True, index=False, sep="|")
        resource.Bucket(bucket).put_object(Key=batchfile,
                                           Body=csv_buffer.getvalue())

        # prep database call to pull the batch file into redshift
        query = copy_query(dbtable, batchfile, log=False)
        logquery = copy_query(dbtable, batchfile, log=True)

        # if truncate is set to true, perform a transaction that will
        # replace the existing table data with the new data in one commit
        if (truncate):
            scratch_start = """
BEGIN;
-- Clean up from last run if necessary
DROP TABLE IF EXISTS {0}_scratch;
DROP TABLE IF EXISTS {0}_old;

-- Create scratch table to copy new data into
CREATE TABLE {0}_scratch (LIKE {0});
ALTER TABLE {0}_scratch OWNER TO microservice;
GRANT SELECT ON {0}_scratch TO looker;\n
""".format(dbtable)
            scratch_copy = copy_query(
                dbtable + "_scratch", batchfile, log=False)
            scratch_copy_log = copy_query(
                dbtable + "_scratch", batchfile, log=True)
            scratch_cleanup = """
-- Replace main table with scratch table, clean up the old table
ALTER TABLE {0} RENAME TO {1}_old;
ALTER TABLE {0}_scratch RENAME TO {1};
DROP TABLE {0}_old;
COMMIT;
""".format(dbtable, table_name)
            query = scratch_start + scratch_copy + scratch_cleanup
            logquery = scratch_start + scratch_copy_log + scratch_cleanup

        logger.debug(logquery)
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as curs:
                try:
                    curs.execute(query)
                # if the DB call fails, print error and place file in /bad
                except psycopg2.Error as e:
                    logger.error("Loading {0} to RedShift failed\n{1}"
                                 .format(batchfile, e.pgerror))
                    outfile = badfile
                # if the DB call succeed, place file in /good
                else:
                    logger.info("Loaded {0} to RedShift successfully"
                                .format(batchfile))
                    outfile = goodfile

        try:
            client.copy_object(
                Bucket="sp-ca-bc-gov-131565110619-12-microservices",
                CopySource="sp-ca-bc-gov-131565110619-12-microservices/"
                + object_summary.key, Key=outfile)
        except boto3.exceptions.ClientError as e:
            logger.exception("S3 transfer failed")
