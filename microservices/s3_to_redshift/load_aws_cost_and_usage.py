###################################################################
# Script Name   : load_aws_cost_and_usage.py
#
# Description   : Script to load AWS Cost and Usage data into Redshift
#
# Requirements  : You must set the following environment variables
#               : to establish credentials for the microservice user
#
#               : export AWS_ACCESS_KEY_ID=<<KEY>>
#               : export AWS_SECRET_ACCESS_KEY=<<SECRET_KEY>>
#               : export pgpass=<<DB_PASSWD>>
#
#
# Usage         : python load_aws_cost_and_usage.py bucket yyyymm
#

import boto3  # s3 access
import re  # regular expressions
import os  # to read environment variables
import psycopg2  # to connect to Redshift
import sys  # to read command line parameters

from operator import attrgetter

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
handler = logging.FileHandler(os.path.join('logs', log_filename), "a", encoding=None, delay="true")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s:%(name)s:%(asctime)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Take two arguments 1. bucket 2. month (eg. 201806)
if (len(sys.argv) != 3):  # will be 1 if no arguments, 2 if one argument
    print "Usage: python load_aws_cost_and_usage.py bucket yyyymm"
    sys.exit(1)
bucket = sys.argv[1]
startmonth = sys.argv[2]
endmonth = str(int(startmonth) + 1)

source = '/aws_cost_and_usage_report/' + startmonth + '01-' + endmonth + '01'
filename = 'aws_cost_and_usage_report-RedshiftCommands.sql'

# set up S3 connection
client = boto3.client('s3')  # low-level functional API
resource = boto3.resource('s3')  # high-level object-oriented API
my_bucket = resource.Bucket(bucket)  # subsitute this for your s3 bucket name.
key = ''

# find the latest file matching "filename"
for object_summary in sorted(my_bucket.objects.filter(Prefix=source),key=attrgetter('last_modified'),reverse=True):
    if re.search(filename, object_summary.key):
        logger.info('\nhttps://s3.console.aws.amazon.com/s3/object/sp-ca-bc-gov-131565110619-12-aws-cost-usage/'
                    + object_summary.key
                    + '\n' + object_summary.last_modified
                    + '\n---')
        key = object_summary.key
        break

obj = client.get_object(Bucket=bucket, Key=object_summary.key)
body = obj['Body']
query = body.read().decode('utf-8')

# update SQL code to include correct credentials and region
query = query.replace("'aws_iam_role=<AWS_ROLE>' region <S3_BUCKET_REGION>", "'aws_access_key_id=" + os.environ['AWS_ACCESS_KEY_ID'] + ";aws_secret_access_key=" + os.environ['AWS_SECRET_ACCESS_KEY'] + "' region 'ca-central-1'")
query = query.replace("AWSBilling" + startmonth, "aws_cost_and_usage.AWSBilling" + startmonth)
query = "DROP TABLE IF EXISTS aws_cost_and_usage.AWSBilling" + startmonth + "; DROP TABLE IF EXISTS aws_cost_and_usage.AWSBilling" + startmonth + "_tagmapping; \n" +  query + "\nGRANT SELECT ON aws_cost_and_usage.awsbilling" + startmonth + " TO looker; GRANT SELECT ON aws_cost_and_usage.awsbilling" + startmonth + "_tagmapping TO looker;"
logger.debug(query)

# prep database call to pull the batch file into redshift
conn_string = "dbname='snowplow' host='snowplow-ca-bc-gov-main-redshi-resredshiftcluster-13nmjtt8tcok7.c8s7belbz4fo.ca-central-1.redshift.amazonaws.com' port='5439' user='microservice' password=" + os.environ['pgpass']
with psycopg2.connect(conn_string) as conn:
    with conn.cursor() as curs:
        try:
            curs.execute(query)
        except psycopg2.Error as e: # if the DB call fails, print error and place file in /bad
            logger.exception("Loading failed\n{0}".format(e.pgerror))
        else:
            logger.info("Loaded successfully")
