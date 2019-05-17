###################################################################
#Script Name    : s3_to_redshift.py
#
#Description    : Microservice script to load a csv file from s3
#               : and load it into Redshift
#
#Requirements   : You must set the following environment variables
#               : to establish credentials for the microservice user
#
#               : export AWS_ACCESS_KEY_ID=<<KEY>>
#               : export AWS_SECRET_ACCESS_KEY=<<SECRET_KEY>>
#               : export pgpass=<<DB_PASSWD>>
#
#
#Usage          : python s3_to_redshift.py configfile.json
#

import boto3 # s3 access
import pandas as pd # data processing
import re # regular expressions
from io import StringIO
from io import BytesIO
import os # to read environment variables
import psycopg2 # to connect to Redshift
import numpy as np # to handle numbers
import json # to read json config files
import sys # to read command line parameters
import os.path #file handling

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
log_filename = '{0}'.format(os.path.basename(__file__).replace('.py','.log'))
handler = logging.FileHandler(os.path.join('logs', log_filename),"a", encoding=None, delay="true")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Read configuration file
if (len(sys.argv) != 2): #will be 1 if no arguments, 2 if one argument
    print "Usage: python s3_to_redshift.py config.json"
    sys.exit(1)
configfile = sys.argv[1]
if (os.path.isfile(configfile) == False): # confirm that the file exists
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
client = boto3.client('s3') #low-level functional API
resource = boto3.resource('s3') #high-level object-oriented API
my_bucket = resource.Bucket(bucket) #subsitute this for your s3 bucket name.

for object_summary in my_bucket.objects.filter(Prefix=source + "/" + directory + "/"):
    if re.search(doc + '$', object_summary.key):
        logger.debug('{0}:{1}'.format(my_bucket.name, object_summary.key))

        # Check to see if the file has been processed already
        batchfile = destination + "/batch/" + object_summary.key
        goodfile = destination + "/good/" + object_summary.key
        badfile = destination + "/bad/" + object_summary.key
        try:
            client.head_object(Bucket=bucket, Key=goodfile)
        except:
            True
        else:
            logger.debug("File processed already. Skip.")
            continue
        try:
            client.head_object(Bucket=bucket, Key=badfile)
        except:
            True
        else:
            logger.debug("File failed already. Skip.")
            continue
        logger.debug("File not already processed. Proceed.")

        obj = client.get_object(Bucket=bucket, Key=object_summary.key)
        body = obj['Body']
        csv_string = body.read().decode('utf-8')


        # Check for an empty file. If it's empty, accept it as good and move on
        try:
            df = pd.read_csv(StringIO(csv_string), sep=delim, index_col=False, dtype = dtype_dic, usecols=range(column_count))
        except Exception as e:
            logger.exception('exption reading {0}'.format(object_summary.key))
            if (str(e) == "No columns to parse from file"):
                logger.warning('File is empty, keying to goodfile and proceeding.')
                outfile = goodfile
            else:
                logger.warning('File not empty, keying to badfile and proceeding.')
                outfile = badfile
            client.copy_object(Bucket="sp-ca-bc-gov-131565110619-12-microservices", CopySource="sp-ca-bc-gov-131565110619-12-microservices/"+object_summary.key, Key=outfile)
            continue

        df.columns = columns

        if 'drop_columns' in data: # Drop any columns marked for dropping
            df = df.drop(columns=drop_columns)

        # Run replace on some fields to clean the data up
        if 'replace' in data:
            for thisfield in data['replace']:
                df[thisfield['field']].replace (thisfield['old'], thisfield['new'])

        # Clean up date fields
        # for each field listed in the dateformat array named "field" apply "format"
        if 'dateformat' in data:
            for thisfield in data['dateformat']:
                df[thisfield['field']] = pd.to_datetime(df[thisfield['field']], format=thisfield['format'])

        # Put the full data set into a buffer and write it to a "|" delimited file in the batch directory
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, header=True, index=False, sep="|")
        resource.Bucket(bucket).put_object(Key=batchfile, Body=csv_buffer.getvalue())

        # prep database call to pull the batch file into redshift
        conn_string = "dbname='snowplow' host='snowplow-ca-bc-gov-main-redshi-resredshiftcluster-13nmjtt8tcok7.c8s7belbz4fo.ca-central-1.redshift.amazonaws.com' port='5439' user='microservice' password=" + os.environ['pgpass']
        query = "copy " + dbtable +" FROM 's3://" + my_bucket.name + "/" + batchfile + "' CREDENTIALS 'aws_access_key_id=" + os.environ['AWS_ACCESS_KEY_ID'] + ";aws_secret_access_key=" + os.environ['AWS_SECRET_ACCESS_KEY'] + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"
        logquery = "copy " + dbtable +" FROM 's3://" + my_bucket.name + "/" + batchfile + "' CREDENTIALS 'aws_access_key_id=" + 'AWS_ACCESS_KEY_ID' + ";aws_secret_access_key=" + 'AWS_SECRET_ACCESS_KEY' + "' IGNOREHEADER AS 1 MAXERROR AS 0 DELIMITER '|' NULL AS '-' ESCAPE;"

        # if truncate is set to true, truncate the db before loading
        if (truncate):
            query = "TRUNCATE " + dbtable + "; " + query
            logquery = "TRUNCATE " + dbtable + "; " + logquery
        logger.debug(logquery)
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as curs:
                try:
                    curs.execute(query)
                except psycopg2.Error as e: # if the DB call fails, print error and place file in /bad
                    logger.error("Loading {0} to RedShift failed\n{1}".format(batchfile,e.pgerror))
                    outfile = badfile       # if the DB call succeed, place file in /good
                else:
                    logger.info("Loaded {0} to RedShift succesfully".format(batchfile))
                    outfile = goodfile

        client.copy_object(Bucket="sp-ca-bc-gov-131565110619-12-microservices", CopySource="sp-ca-bc-gov-131565110619-12-microservices/"+object_summary.key, Key=outfile)
