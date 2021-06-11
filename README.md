## GDX Analytics

[![img](https://img.shields.io/badge/Lifecycle-Maturing-007EC6)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)

---
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

#### [maintenance/](./maintenance/)

- Scripts for internal use to assist in regular maintenance procedures on EC2 instances or other services.

#### [operations/](./operations/)

- scripts to perform one-off on-demand operational tasks.

#### [testing/migration_tests/](./testing/migration_tests/)

- Scripts to provide better automation and coverage on the testing strategy of the WebTrends to Snowplow migration.

#### [web_trackers/](./web_trackers/)

- Examples of the Javascript tracker used to push custom events to Snowplow;

## Relevant Repositories

All GDX Analytics repositories can be found in the [bcgov](https://github.com/bcgov/) GitHub organization with the topic: [#gdx-analytics](https://github.com/topics/gdx-analytics).

#### [GDX-Analytics-microservice/](https://github.com/bcgov/GDX-Analytics-microservice)

The collection of GDX-Analytics Python microservices used to load and process data between systems and services.

#### [GDX-Analytics-Looker-cfms_block/](https://github.com/bcgov/GDX-Analytics-Looker-cfms_block)

Represents an instance of the Government of British Columbia’s Service BC [LookML](https://docs.looker.com/data-modeling/learning-lookml/what-is-lookml) project.

#### [GDX-Analytics-Looker-Redshift_Admin_By_AWS/](https://github.com/bcgov/GDX-Analytics-Looker-Redshift_Admin_By_AWS)

Provides a substitute for the AWS Console, helping users identify how tables are structured and if data flow is normal.

#### [GDX-Analytics-Looker-Snowplow-Web-Block/](https://github.com/bcgov/GDX-Analytics-Looker-Snowplow-Web-Block)

Represents an instance of the Government of British Columbia’s Web Analytics [LookML](https://docs.looker.com/data-modeling/learning-lookml/what-is-lookml) project.

#### [GDX-Analytics-Looker-theq_sdpr_block/](https://github.com/bcgov/GDX-Analytics-Looker-theq_sdpr_block)

The GDX Analytics LookML project to support SDPR's TheQ implementation.

#### [GDX-Analytics-OpenShift-Snowplow-Gateway-Service/](https://github.com/bcgov/GDX-Analytics-OpenShift-Snowplow-Gateway-Service)

A gateway service to handle event analytics for BC Government projects on the OpenShift cluster.

#### [GDX-Analytics-Drupal_snowplow/](https://github.com/bcgov/GDX-Analytics-Drupal-Snowplow)

A Drupal 8 module that runs the GDX-Analytics Snowplow web trackers.

#### [GDX-Analytics-Looker-Google-Block/](https://github.com/bcgov/GDX-Analytics-Looker-Google-Block)

This is for the Government of British Columbia’s instance their Google API LookML project. LookML is a language for describing dimensions, aggregates, calculations and data relationships in a SQL database

## Getting Help or Reporting an Issue

For inquiries about starting a new analytics account please contact the GDX Analytics Team.

## Contributors

The GDX Analytics Team are the main contributors to this project.

## How to Contribute

If you would like to contribute, please see our [CONTRIBUTING](CONTRIBUTING.md) guideleines.

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

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
