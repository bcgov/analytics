###################################################################
# Script Name       : elasticsearch_tail.py
#
# Description       : Simulates a unix like tail command for Elasticsearch
#
# Requirements      : Install the requirements to a python2 virtualenv:
#
#                   : virtualenv -p python2 venv
#                   : source venv/bin/activate
#                   : pip install -r requirements.txt
#
# Recommendations   : It's recommended to set environment variables for
#                   : the ES endpoint, credentials, and index for regular use
#
#                   : export ES_USER='<<ElasticSearch_Username>>'
#                   : export ES_PASS='<<ElasticSearch_Password>>'
#                   : export ES_ENDPOINT='<<ElasticSearch_Endpoint>>'
#                   : export ES_INDEX='<<ElasticSearch_Index>>'
#
# Usage             : To tail nonstop run:
#                   : python elasticsearch_tail.py --endpoint $ES_ENDPOINT
#                   :   --index $ES_INDEX --username $ES_USER --password
#                   :   $ES_PASS -application <app_id>
#                   : To end, use Ctrl+c
#                   :

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import logging
import sys
import os
from argparse import ArgumentParser
import signal  # Dealing with Ctrl+C
from sets import Set

# Arguments parsing
parser = ArgumentParser(
    description='Unix like tail command for Elastisearch and Snowplow.')
parser.add_argument('-e', '--endpoint', help='ES endpoint URL.', required=True)
parser.add_argument('-i', '--index', help='Index name.', required=True)
parser.add_argument('-d', '--debug', help='Debug', action="store_true")
parser.add_argument('-u', '--username', help='Username. Requires --password')
parser.add_argument('-p', '--password', help='Password. Requires --username')
parser.add_argument('-a', '--application', help='The application.')
parser.add_argument('-c', '--config', help='Config file listing the fields of \
                    interest.', required=True)
args = parser.parse_args()


# Ctrl+C
def signal_handler(signal, frame):
    logger.debug('Ctrl+C pressed!')
    sys.exit(0)


######
# Main
######

# Ctrl+C handler
signal.signal(signal.SIGINT, signal_handler)

# Create stream handler for logs at the INFO level
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s:[%(levelname)s]: %(message)s")
logger.setLevel(logging.INFO)
if args.debug:
    # Extend stream handler for logs at the DEBUG level
    logger.setLevel(logging.DEBUG)
    logger.debug("debug mode is on")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# ARGS
# --endpoint (required)
endpoint = args.endpoint
logger.debug("endpoint: " + endpoint)

# --application (required)
# checks against known applications
application = args.application
logger.debug("application: " + application)

known_applications = ['TheQ',
                      'Snowplow_gov',
                      'Snowplow_standalone',
                      'Snowplow_standalone_MyFS',
                      'Snowplow_engage']

if application not in known_applications:
    logger.warning('The application "{0}" is not in the list of known \
                   applications.')

# --index (required)
index = args.index
logger.debug("index: " + index)

# -- username and password: must be neither or both
if args.username:
    http_user = args.username
    if args.password:
        http_pass = args.password
        logger.debug("username: " + http_user)
        logger.debug("password provided")
    else:
        parser.error("--username requires --password.")
elif args.password:
    parser.error("--password requires --username.")

if http_user and http_pass:
    es = Elasticsearch([endpoint], http_auth=(http_user, http_pass))

# make tuple from lines in config file
config = args.config
if os.path.isfile(config):
    with open(config) as f:
        fields = tuple(line.rstrip() for line in f)
    logger.debug("fields: {0}".format(fields))
else:
    logger.error("a config file listing fields by line is required. \
                 Use --config <file_path>")
# Using two sets to control for duplicate events scanned from one loop to next
hits = Set()
last_hits = Set()
hit_count = 0
while True:
    s = Search(using=es, index=index)

    # TODO:
    # The collector_tstamp is being used in place of an incremental index.
    # When an incremental index is known we should refactor to only events that
    # have that field higher than the last printed.

    # This approach executes queries on the collector_tstamp
    # qry = Q('term', app_id=application)
    # s = s[:1].filter(qry).sort('collector_tstamp')
    # count = s.count()
    # result = s.execute()
    # print(result.success())
    # print(result.took)
    # for hit in result:
    #     logline = "hit".format(hit_count)
    #     for i in fields:
    #         logline += "\n - {0}: {1}".format(i, hit[i])
    #     logger.info(logline)

    qry = Q('term', app_id=application)\
        & Q('range', collector_tstamp={'gte': 'now-15s'})
    s = s.filter(qry)  # .sort('collector_tstamp')

    # scan() does not support sort queries
    for hit in s.scan():
        t = (hit.collector_tstamp, hit.event_id)
        hits.add(t)
        if t in last_hits:
            logger.debug(hit.event_id + " already exists")
            continue
        hit_count += 1
        logline = "hit {0}".format(hit_count)
        for i in fields:
            logline += "\n - {0}: {1}".format(i, hit[i])
        logger.info(logline)
    last_hits = hits.copy()
    hits.clear()
