## GDX Analytics

This is the central repository for work by the GDX Analytics Team. 

## Features

The GDX Analytics Service uses [Snowplow](http://snowplowanalytics.com/) and [Looker](http://looker.com/) to provide analytics for online and offline service delivery. 

## Project Status

This project is currently under development and actively supported by the GDX Analytics Team.

## Contents by Directory:

#### [examples/](./examples/)

- Proof of concept examples of the code required to add Snowplow instrumentation client applications;
- Embed generators in Java and Python demonstrating the generation of cryptographically signed SSO embed URL;
- The `s3-upload.sh` script, to upload files to S3 with standard Unix utilities, for example: to run as a cron job and load scheduled data dumps;
- Snowplow schema files.

#### [microservices/](./microservices/)

- Microservices running on EC2 to perform automated data loads of well formed data into RedShift.

#### [web_trackers/](./web_trackers)

- Examples of the Javascript tracker used to push custom events to Snowplow;

#### [testing/](./testing/)

- Scripts automating the testing strategies of the WebTrends to Snowplow migration.

#### [maintenance/](./maintenance/)

- Scripts for internal use to assist in regular maintenance procedures on EC2 instances or other services.

## Relevant Repositories

#### [GDX-Analytics-Looker-AWS-Cost-And-Usage/](https://github.com/bcgov/GDX-Analytics-Looker-AWS-Cost-And-Usage)

Provides GDX Analytics with reporting to track AWS usage, estimated charges, and line items by AWS product, usage type, and operation.

#### [GDX-Analytics-Looker-cfms_block/](https://github.com/bcgov/GDX-Analytics-Looker-cfms_block)

Represents an instance of the Government of British Columbia’s Service BC [LookML](https://docs.looker.com/data-modeling/learning-lookml/what-is-lookml) project.

#### [GDX-Analytics-Looker-Redshift_Admin_By_AWS/](https://github.com/bcgov/GDX-Analytics-Looker-Redshift_Admin_By_AWS)

Provides a substitute for the AWS Console, helping users identify how tables are structured and if data flow is normal.

#### [GDX-Analytics-Looker-Snowplow-Web-Block/](https://github.com/bcgov/GDX-Analytics-Looker-Snowplow-Web-Block)

Represents an instance of the Government of British Columbia’s Web Analytics [LookML](https://docs.looker.com/data-modeling/learning-lookml/what-is-lookml) project.

#### [GDX-Analytics-Looker-Webtrends-Testing-Block/](https://github.com/bcgov/GDX-Analytics-Looker-Webtrends-Testing-Block)

Represents the testing related to migration of Government of British Columbia’s data from WebTrends to Looker/Snowplow using [LookML](https://docs.looker.com/data-modeling/learning-lookml/what-is-lookml).

#### [GDX-Analytics-Looker-theq_sdpr_block/](https://github.com/bcgov/GDX-Analytics-Looker-theq_sdpr_block)

The GDX Analytics LookML project to support SDPR's TheQ implementation.

#### [GDX-Analytics-OpenShift-Snowplow-Gateway-Service/](https://github.com/bcgov/GDX-Analytics-OpenShift-Snowplow-Gateway-Service)

A gateway service to handle event analytics for BC Government projects on the OpenShift cluster.

#### [GDX-Analytics-Drupal_snowplow/](https://github.com/bcgov/GDX-Analytics-Drupal-Snowplow)

A Drupal 8 module that runs the GDX-Analytics Snowplow web trackers.

#### [GDX-Analytics-Looker-Google-Block](https://github.com/bcgov/GDX-Analytics-Looker-Google-Block)

This is for the Government of British Columbia’s instance their Google API LookerML project. LookerML is a language for describing dimensions, aggregates, calculations and data relationships in a SQL database

## Getting Help

For Web Analytics help, please contact the GDX Service Desk via [GCPE GDX Client Service Desk Portal](https://apps.gcpe.gov.bc.ca/jira/servicedesk/customer/portal/9). For inquiries about starting a new analytics account please contact the GDX Analytics Team.

## Contributors

The GDX Analytics Team are the main contributors to this project.

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
