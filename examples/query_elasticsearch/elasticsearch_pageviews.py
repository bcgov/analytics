###################################################################
# Script Name       : elasticsearch_pageviews.py
#
# Description       : Counts page views from 1 Hour previous for Elasticsearch
#                     and Snowplow.
#
# Requirements      : Install the following python packages to allow
#                     querying the elasticsearch endpoint
#
#                   : elasticsearch-dsl>=6.0.0,<7.0.0
#                   : elasticsearch>=6.0.0,<7.0.0
#
# Recommendations   : It's recommended to set environment variables for
#                     the elastic search endpoint.
#
#                   : export ES_USER='<<ElasticSearch_Username>>'
#                   : export ES_PASS='<<ElasticSearch_Password>>'
#
# Usage             : To query a list of domains, run:
#
#                   : python3 elasticsearch_pageviews.py -c domainlist.txt
#                   :   -u ES_USER -p ES_PASS
#
#                   : where 'domainlist.txt' is a text file containing the
#                   : newline separated list of domains you wish to query.
#                   : You can optionally specify a start time and an end
#                   : time using flags:
#
#                   : python3 elasticsearch_pageviews.py -c domainlist.txt
#                   :   -u ES_USER -p ES_PASS -s 'now-60m' -e 'now'

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import logging
from argparse import ArgumentParser
import sys
import os
import signal

# Arguments parsing
parser = ArgumentParser(
  description='Counts page views for given domains using Elastisearch \
               and Snowplow.')
parser.add_argument('-c', '--config', help='Config file listing the domains \
                    of interest.', required=True)
parser.add_argument('-s', '--starttime', help='Start time.')
parser.add_argument('-e', '--endtime', help='End time.')
parser.add_argument('-u', '--username', help='Username.', required=True)
parser.add_argument('-p', '--password', help='Password.', required=True)
parser.add_argument('-d', '--debug', help='Debug', action="store_true")
args = parser.parse_args()


# Ctrl+C
def signal_handler(signal, frame):
    logger.debug('Ctrl+C pressed!')
    sys.exit(0)


# Ctrl+C handler
signal.signal(signal.SIGINT, signal_handler)

# Create stream handler for logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s:[%(levelname)s]: %(message)s")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

config = args.config
if os.path.isfile(config):
    with open(config) as f:
        domains = tuple(line.rstrip() for line in f)
else:
    logger.error("a config file listing domains by line is required. \
                 Use --config <file_path>")
if(args.starttime):
    starttime = args.starttime
else:
    starttime = 'now-60m'
if(args.endtime):
    endtime = args.endtime
else:
    endtime = 'now'

http_user = args.username
http_pass = args.password
endpoint = "https://ca-bc-gov-elasticsearch-1.analytics.snplow.net"

client = Elasticsearch(endpoint, http_auth=(http_user, http_pass))
logger.debug('Elastic search object: ', client)

good_index = 'ca-bc-gov-main-snowplow-good-query-alias'
bad_index = 'ca-bc-gov-main-snowplow-bad-query-alias'

for domain in domains:
    # this query parameter looks at the last hour (now-60) where the Page URL
    # Host was inserted with Host was inserted with the domain variable
    params = Q('term', page_urlhost=domain) & \
             Q('range', derived_tstamp={'gte': starttime}) & \
             Q('term', event='page_view') & \
             Q('range', derived_tstamp={'lt': endtime})

    try:
        s = Search(using=client, index=good_index).filter(params)
    except Exception as e:
        logger.debug(e)
    # we actually don't need to aggregate; the query filter itself
    # contains this information.
    count = s.count()

    logger.info(domain + ' page views successfully queried')
    print ('Domain: ', domain, ' Page Views: ', count)
