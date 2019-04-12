## GDX Analytics Snowplow Web Tracker Code

This code demonstrates the inline Javascript to track web analytics events for CMS Lite, Wordpress, Search, and Standalone sites. **Please Confirm with GDX Analytics before adding the tracker to your website.** 

It will connects to Snowplow Mini, which is used for development and testing. Once ready, the GDX Analytics Team will help you update it to the push data to the production Snowplow pipeline. 

## Trackers
* [`gov_sp_script.js`](./gov_sp_script.js) should only be used by CMS Lite. It includes a custom context to capture the Node ID of the current page. 
* [`gov_search_sp_script.js`](./gov_search_sp_script.js) should only be used for Search pages in CMS Lite.
* [`wordpress_sp_script.js`](./wordpress_sp_script.js) should be used by sites using the standard Wordpress setup. This includes Engage.gov sites and Standalone sites. 
* [`Snowplow_inline_code.js`](./Snowplow_inline_code.js) can be placed on any Standalone site that uses GDX Analytics services that does not have a search function.
* [`Snowplow_inline_code_search.js`](./Snowplow_inline_code_search.js) can be placed on any Standalone site that uses GDX Analytics services and has a search fuction. This script requires the variable `searchParameter` be assigned to match the search query parameter on your site. In most cases the search query parameter is `'q'`, and in the case of Wordpress it is `'s'`.

   For example, if you were placing this tracker on a Wordpress site then:
   ```javascript
   var searchParameter = 'Search term parameter'
   ```
   should be reassigned as:
   ```javascript
   var searchParameter = 's'
   ```

## Versioning
The tracker version will be of the form `vX.A.B.C`, where `X` refers to the GDX Analytics release and `A.B.C` refers to the Snowplow Javascript version.

## Project Status

Currently this project is in development.

## To Run
**Please Confirm with GDX Analytics before adding the tracker to you website.**   
Add this script in the header section of the html page in a `<script type="text/javascript">` block. 

This script connects to the test instance of Snowplow (Snowplow Mini). When the testing is completed, the collector must be changed to use the main Snowplow pipeline. Please contact the GDX Analytics Team for instructions to move to the production version. **NOTE:** You should not use the test version on a production site. 

## Getting Help

Please contact ryan.janes@gov.bc.ca for questions related to this work. 

## Contributors

The GDX Analytics Team will be the main contributors to this project currently and will maintain the code. 

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

