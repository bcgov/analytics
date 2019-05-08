## S3 Upload Utility 

The [s3-upload.sh](s3-upload.sh) bash script lets you upload files to s3 without installing any additional tools beyond standard Unix utilities. 

## Project Status

Currently this project is still in development.

## Dependencies

`curl`, `openssl 1.x`, `GNU sed`, LF EOLs in this file.

## To Run

You must set two environment variables
```
$ export AWS_ACCESS_KEY_ID="<<AWS_KEY>>"
$ export AWS_SECRET_ACCESS_KEY="<<AWS_SECRET_KEY>>
```

And run

```
$ sh s3-upload.sh <<localfile>> <<bucket>> <<remotepath>> <<region>> <<OPTIONAL:storageclass>>
```

For example:

```
$ sh s3-upload.sh  local/path/foo.csv  bucket-name remote/path ca-central-1
```

will upload the file "`foo.csv`" in the local directory "`local/path`" and place it in s3 in "`ca-central-1`" at "`bucket-name/bucket-name/remote/path/foo.csv`".

## Getting Help

Please contact dan.pollock@gov.bc.ca for questions related to this work.

## Contributors

The GDX analytics team will be the main contributors to this project currently. They will also maintain the code. This is based on [vszakats/s3-upload.sh](https://gist.github.com/vszakats/2917d28a951844ab80b1)

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
