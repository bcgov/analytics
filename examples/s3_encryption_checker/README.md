## S3 Encryption Checker

The [s3_encryption_checker.py](s3_encryption_checker.py) python script searches through an S3 bucket to detect any objects that are not encrypted. It is a good, relatively simple, example of how to programmatically access S3 using [Boto](http://boto.cloudhackers.com/en/latest/).

## Project Status

Currently this project is still in development.

## Dependencies

Python libraries `boto3`, `sys`

## To Run

You must set two environment variables
```
$ export AWS_ACCESS_KEY_ID="<<AWS_KEY>>"
$ export AWS_SECRET_ACCESS_KEY="<<AWS_SECRET_KEY>>
```

And run
```
$ python s3_encryption_checker.py bucket
```
or
```
$ python s3_encryption_checker.py bucket prefix
```

## Getting Help

Please contact dan.pollock@gov.bc.ca for questions related to this work. 

## Contributors

The GDX analytics team will be the main contributors to this project currently. They will also maintain the code. 


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

