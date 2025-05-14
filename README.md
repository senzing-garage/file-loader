# file-loader

If you are beginning your journey with [Senzing],
please start with [Senzing Quick Start guides].

You are in the [Senzing Garage] where projects are "tinkered" on.
Although this GitHub repository may help you understand an approach to using Senzing,
it's not considered to be "production ready" and is not considered to be part of the Senzing product.
Heck, it may not even be appropriate for your application of Senzing!

## Overview

file-loader is a Python utility to load [Senzing mapped JSON data], once loading is complete [redo records] are processed. file-loader can be run as a Docker container or standalone.

```console
usage: file-loader.py [-h] [-f [file]] [-cj [config]] [-i] [-t] [-nt num_threads]

Utility to load Senzing JSON records and process redo records

optional arguments:
  -h, --help            show this help message and exit
  -f [file], --file [file]
                        Path and name of file to load.

                        Default: None, must be specified.
                        Env Var: SENZING_INPUT_FILE

  -cj [config], --configJson [config]
                        JSON string of the Senzing engine configuration.

                        Default: None, must be specified.
                        Env Var: SENZING_ENGINE_CONFIGURATION_JSON

  -i, --info            Produce withInfo messages and write to a file

                        Default: False
                        Env Var: SENZING_WITHINFO

  -t, --debugTrace      Output debug trace information.

                        Default: False
                        Env Var: SENZING_DEBUG

  -nt num_threads, --numThreads num_threads
                        Total number of worker threads performing load.

                        Default: Calculated based on hardware.
                        Env Var: SENZING_THREADS_PER_PROCESS


Arguments can be specified with either CLI arguments or environment variables, some arguments have
default values.

The order of precedence for selecting which value to use is:

  1) CLI Argument
  2) Environment variable
  3) Default value if available

For additional help and information: https://github.com/senzing-garage/file-loader/blob/main/README.md
```

# APIs Demonstrated

## Core

- addRecord[WithInfo]: Adds the Senzing JSON record
- getRedoRecord: Fetch a redo record to process
- processRedoRecord[WithInfo]: Process a redo record

## Supporting

- init: To initialize engine objects
- destroy: To destroy engine objects
- getConfigList: To get configuration details
- getActiveConfigID: To get the active config ID
- getDBInfo: To get database information
- license: To get license information
- version: To get version information
- stats: To retrieve internal engine diagnostic information as to what is going on in the engine

# Details

Parameters to file-loader can be specified as either environment variables or CLI arguments.

## Required Parameters (Environment)

- SENZING_ENGINE_CONFIGURATION_JSON

## Optional Parameters (Environment)

- SENZING_INPUT_FILE
- SENZING_WITHINFO
- SENZING_DEBUG
- SENZING_THREADS_PER_PROCESS

For details and defaults of the optional parameters see the help information.

## Running

### Data Source

Ensure any DATA_SOURCE values used in the files to load exist in the Senzing configuration with G2ConfigTool. For details of how to add them, see [Quickstart For Docker].

### Docker

Export SENZING_ENGINE_CONFIGURATION_JSON, modify CONNECTION details to your database.

```console
export SENZING_ENGINE_CONFIGURATION_JSON='{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "postgresql://senzing:password@myhost:5432:g2"
  }
}'
```

```console
docker run -it --rm -u $UID -v ${PWD}:/data -e SENZING_ENGINE_CONFIGURATION_JSON senzing/file-loader -f /data/customers.json
```

The above example assumes the customers.json file is in the current path where the command is being executed from.

## Additional Items to Note

- Docker `--volume (-v)` is used to mount the host path where the input file to load is located within the container at `/data`. Any error or with info files will also be written to the same host path.
- If no input file is specified, loading will be skipped and redo record processing will be processed.
- The number of threads to use is automatically estimated for loading and processing redo records. If the Senzing database is also running on the same machine and you notice very high CPU load, you can reduce the number of threads with the CLI argument `--numThreads` or the `SENZING_THREADS_PER_PROCESS` environment variable. To know how many threads a run started with look for a similar message during startup:

```console
2022-12-08 15:58:39,045 - file-loader - INFO:  Starting to load with 12 threads...
```

- If you have a Senzing license, this can be specified in the JSON configuration with the `LICENSESTRINGBASE64` key.

````console
```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data",
    "LICENSESTRINGBASE64": "<base64_string>"
  },
  "SQL": {
    "CONNECTION": "postgresql://senzing:password@host:5432:g2"
  }
}
````

[Quickstart For Docker]: https://senzing.zendesk.com/hc/en-us/articles/12938524464403-Quickstart-For-Docker
[redo records]: https://senzing.zendesk.com/hc/en-us/articles/360007475133-Processing-REDO
[Senzing Garage]: https://github.com/senzing-garage
[Senzing mapped JSON data]: https://senzing.zendesk.com/hc/en-us/articles/231925448-Generic-Entity-Specification
[Senzing Quick Start guides]: https://docs.senzing.com/quickstart/
[Senzing]: https://senzing.com/
