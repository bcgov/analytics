## Google Search API Loader Microservice

The `google_search.py` script automates the loading of Google Search API data into S3 (as `.csv`) and Redshift (the `google.googlesearch` schema as defined by `google.googlesearch.sql`).

The accompanying `google_search.json` configuration file specifies the bucket, schema, the sites to query the Google Search API for, and optional start dates on those sites.

The microservice will begin loading Google data from the date specified in the configuration as `"start_date_default"`. If that is unspecified, it will attempt to load data from 16 months ago relative to the script runtime. If more recent data already exists; it will load data from the day after the last date that has already been loaded into Redshift.

It currently runs in batches of a maximum of 30 days at a time until 2 days ago (the latest available data from the Google Search API).

### Configuration

The JSON configuration is loaded as an environmental variable defined as `GOOGLE_MICROSERVICE_CONFIG`. It follows this structure:

- `"bucket"`: a string to define the S3 bucket where CSV Google Search API query responses are stored.
- `"dbtable"`: a string to define the Redshift table where the S3 stored CSV files are inserted to to after their creation.
- `"sites"`: a JSON array containing objects defining a `"name"` and an optional `"start_date_default"`.
  - `"name"`: the site URL to query the Google Search API on.
  - `"start_date_default"`: an _optional_ key identifying where to begin queries from as a YYYY-MM-DD string. If excluded, the default behaviour is to look back to the earliest date that the Google Search API exposes, which is 16 months (scripted as 480 days).

```
{
    "bucket": string,
    "dbtable": "google.googlesearch",
    "sites":[
        {
        "name":"https://www2.gov.bc.ca/"
        }
    ]
}
```

## Google My Business API Loader microservice
The `google_mybusiness.py` script pulling the Google My Business API data for locations according to the accounts specified in `google_mybusiness.json`. The metrics from each location are consecutively recorded as `.csv` files in S3 and then copied to Redshift.

Google makes location insights data available for a time range spanning 18 months ago to 2 days ago. The script iterates each location for the date range specified on the date range specified by config keys `start_date` and `end_date`. If no range is set (those key values are left as blank strings), then the script attempts to query for the full range of data availability.

### Configuration

- `"bucket"`: a string to define the S3 bucket where CSV Google My Business API query responses are stored.
- `"dbtable"`: a string to define the Redshift table where the S3 stored CSV files are copied to to after their creation.
- `"metrics"`: an list containing the list of metrics to pull from Google My Business
- `"locations"`: an object that annotates account information from clients that have provided us access”
  - `"client_shortname"`: the client name to be recorded in the client column of the table for filtering
  - `"name"`: The account Name label
  - `"names_replacement"`: An list to replace matched values from the locations under this account as suggested by: `['find','replace']`. For example, in the case of Service BC, all locations are prefixed with "Service BC Centre". We replace this with nothing in order to get _just_ the unique names.
  - `"id"`: the account ID, used for validation when querying the API.
  - `"start_date"`: the query start date as `"YYYY-MM-DD"`, leave as `""` to get the oldest data possible (18 months ago)
  - `"end_date"`: the query end date as `"YYYY-MM-DD"`, leave as `""` to get the most recent data possible (2 days ago) 


## Project Status

Currently microservice itself is implemented. As sites provide GDX Analytics with access to their Google Search APIs, they will be added to the configuration file to be handled by the microservice.

## Getting Help

Please Contact the GDX Service desk for any analytics service help. For inquiries about Google Search API integration or for inquiries about starting a new analytics account for Government, please contact The GDX Analytics team.

## Contributors

The GDX analytics team will be the main contributors to this project currently and will maintain the code.

## License

Copyright 2015 Province of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
