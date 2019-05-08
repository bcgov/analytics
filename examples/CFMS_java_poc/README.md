## GDX Analytics CFMS Instrumentation Proof of Concept 

This code is a proof of concept of Java code required to add Snowplow instrumentation to the CFMS application. For more information on the Snowplow Java Tracker see https://github.com/snowplow/snowplow-java-tracker.

## Project Status

Currently this project is still in development.

## To Build and Run

```
$ gradle build
$ java -jar build/libs/CFMS_java_poc-all-0.5.jar
```

## To download all dependencies to the "runtime" directory

```
$ gradle getDeps
```

## A note for Maven users

Snowplow may be particular about library versions you are using. You may need to add these lines to your pom.xml file

### In the &lt;dependencies> section:
```
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>${jackson.version}</version>
</dependency>
 
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-annotations</artifactId>
    <version>${jackson.version}</version>
</dependency>
 
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-core</artifactId>
    <version>${jackson.version}</version>
</dependency>
```

### In a  &lt;properties> section, after  &lt;dependencies>:
```
<properties>
        <jackson.version>2.4.1</jackson.version>
              <src.dir>src</src.dir>
              <maven.compiler.source>1.8</maven.compiler.source>
              <maven.compiler.target>1.8</maven.compiler.target>
              <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>
```

## Special files in this repository
The files in [../../schemas/ca.bc.gov.cfmspoc](../../schemas/ca.bc.gov.cfmspoc) are the Snowplow schema files. See https://github.com/snowplow/iglu for more info.

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

