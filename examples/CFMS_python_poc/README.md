## GDX Analytics Python Example

### [sn.py](./sn.py)
This code is a proof of concept of Python code required to add Snowplow instrumentation using the initial CFMS proof of concept model. For more information on the Snowplow Python Tracker see https://github.com/snowplow/snowplow-python-tracker.

### [call_analytics_openshift_gateway.py](./call_analytics_openshift_gateway.py)
Sample Python script showing the structure of an example event, and the requirements to call the GDX Analytics OpenShift Snoplow Gateway service with that event data. See https://github.com/bcgov/GDX-Analytics-OpenShift-Snowplow-Gateway-Service

- [call_analytics_openshift_gateway.py](./call_analytics_openshift_gateway.py) creates a json object to POST to the GDX Analytics OpenShift Snoplow Gateway service. An example of the *kind* of JSON event that service can accept is also provided here as [post_data.json](./post_data.json). This file may be helpful for tests of the service using tools like [Postman](https://www.getpostman.com/) or [Insomnia](https://insomnia.rest/), or simply using cURL as:
```
curl -vX POST <<hostname>> -d @post_data.json --header "Content-Type: application/json"
```

## Project Status

Currently this project is still in development.

## Requirements

If running [sn.py](./sn.py), you will first need to install the [snowplow-tracker](https://pypi.org/project/snowplow-tracker/) package:
```
$ sudo pip install snowplow-tracker
```

*Note:* this package is not required to use analytics when calling the [GDX-Analytics OpenShift Snowplow Gateway Service](https://github.com/bcgov/GDX-Analytics-OpenShift-Snowplow-Gateway-Service) tracker such as through [call_analytics_openshift_gateway.py](./call_analytics_openshift_gateway.py). The only dependencies are: [http.client](https://docs.python.org/3/library/http.client.html), [time](https://docs.python.org/3/library/time.html), and [json](https://docs.python.org/3/library/json.html) from the Python Standard Library.

## To Run

To run  [sn.py](./sn.py):
```
$ python sn.py
```

To run [call_analytics_openshift_gateway.py](./call_analytics_openshift_gateway.py):
```
$ python call_analytics_openshift_gateway.py <<hostname>> [<<hostport>>]
```
- Likely values for the `<<hostname>>` argument are `caps.pathfinder.gov.bc.ca` (the production OpenShift route) or `0.0.0.0` (if testing locally).
- Likely values for the `[<<hostport>>]` optional argument are `8080` (if testing locally).
- Note that the GDX Analytics OpenShift Snowplow Gateway Service is currently whitelisted to allow only BC Government IP ranges (including the IP ranges for OpenShift itself).

## Special files in this repository
The files in [examples/schemas/ca.bc.gov.cfmspoc](../schemas/ca.bc.gov.cfmspoc) are the Snowplow schema files. See https://github.com/snowplow/iglu for more info.

## If you encounter an SSL certificate error
When connecting to Snowplow signed by a BC Government SSL certificate you may encounter this Python error:
```
WARNING:snowplow_tracker.emitters:[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:833)
```
This occurs on some systems where your Python environment is missing the root certificate used to sign our SSL certificate. It appears that the Certificate Authority (CA) for Entrust is missing. 

You can test this on the main HTTPS certificate using an interactive Python session by running: 
```
>>> import requests
>>> requests.get('https://www2.gov.bc.ca')
```

To work around this issue, download the CA from https://www.entrustdatacard.com/pages/root-certificates-download. 
Look for the "Entrust Root Certificate Authority—G2" and dowload the certificate from https://entrust.com/root-certificates/entrust_g2_ca.cer. 

To ensure that Python loads this CA, can set this environment variable:
```
# export REQUESTS_CA_BUNDLE=/path/to/entrust_g2_ca.cer
```

## Getting Help

Please Contact dan.pollock@gov.bc.ca for questions related to this work. 

## Contributors

The GDX analytics team will be the main contributors to this project currently. They will also maintain the code as well. 

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

