## GDX Analytics Elastisearch Query Example

### [elasticsearch_tail.py](./elasticsearch_tail.py)
Simulates a unix like tail command for Elasticsearch

Configuration file should contain line separated list of fields to query from the Elasticsearch index and application specified.

It's recommended to set environment variables for the ES endpoint, credentials, and index for regular use:

```
export ES_USER='<<ElasticSearch_Username>>'
export ES_PASS='<<ElasticSearch_Password>>'
export ES_ENDPOINT='<<ElasticSearch_Endpoint>>'
export ES_INDEX='<<ElasticSearch_Index>>'
```

It's also recommended to run a Python 2.7 virtual environment to install the required packages on:

```
virtualenv -p python2 venv
source venv/bin/activate
pip install -r requirements.txt
```

Usage example including optional `--debug`:
```
python elasticsearch_tail.py --endpoint $ES_ENDPOINT --index $ES_INDEX --username $ES_USER --password $ES_PASS --application <app_id> --config <config_file> --debug
```

A sample result will appear as (the following is not real data):
```
2019-05-25 21:47:56,794:[DEBUG]: endpoint: https://ca-bc-gov-elasticsearch-1.analytics.snplow.net
2019-05-25 21:47:56,794:[DEBUG]: application: Snowplow_gov
2019-05-25 21:47:56,794:[DEBUG]: index: ca-bc-gov-main-snowplow-good-query-alias
2019-05-25 21:47:56,794:[DEBUG]: username provided
2019-05-25 21:47:56,794:[DEBUG]: password provided
2019-05-25 21:47:56,795:[DEBUG]: fields: ('collector_tstamp', 'event_id', 'event_name')
2019-05-25 21:48:06,213:[INFO]: hit 1
 - collector_tstamp: 2019-05-26T04:47:53.781Z
 - event_id: 07114185-a0ff-46ee-8a25-6d3b8a475dd0
 - event_name: page_view
```
