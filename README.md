 # file-loader

 ## Overview

file-loader.py is a Python utility to load [Senzing mapped JSON data](https://senzing.zendesk.com/hc/en-us/articles/231925448-Generic-Entity-Specification), once loading is complete [redo records](https://senzing.zendesk.com/hc/en-us/articles/360007475133-Processing-REDO) are processed.


```console
usage: file-loader.py [-h] [-f [file]] [-cj [config]] [-i] [-t] [-nt num_threads] [-if [file]] [-ef [file]]

Utility to load Senzing JSON records and process redo records

options:
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
                        
  -if [file], --infoFile [file]
                        
                        Path/file to write with info data to.
                        
                        Default: file-loader_withInfo_20221208_135944.jsonl
                        Env Var: SENZING_WITHINFO_FILE
                        
  -ef [file], --errorsFile [file]
                        
                        Path/file to write errors to.
                        
                        Default: file-loader_errors_20221208_135944.log
                        Env Var: SENZING_ERRORS_FILE
                        

Arguments can be specified with either CLI arguments or environment variables, some arguments have 
default values.
        
The order of precedence for selecting which value to use is:
        
  1) CLI Argument
  2) Environment variable
  3) Default value if available
  
For additional help and information: https://github.com/Senzing/file-loader/blob/main/README.md
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
- SENZING_INPUT_FILE

## Optional Parameters (Environment)
- SENZING_WITHINFO
- SENZING_DEBUG
- SENZING_THREADS_PER_PROCESS
- SENZING_WITHINFO_FILE 
- SENZING_ERRORS_FILE

For details and defaults of the optional parameters see the help information. 

Note: SENZING_WITHINFO_FILE and SENZING_ERRORS_FILE are only valid when running on a Senzing bare metal install not via Docker.

## Running

### Data Source
Ensure any DATA_SOURCE values used in the files to load exist in the Senzing configuration with G2ConfigTool.

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
docker run -it --rm -u $UID -v ${PWD}:/input -v ${PWD}:/output -e SENZING_ENGINE_CONFIGURATION_JSON senzing/file-loader -f /input/customers.json
```
The above example assumes the customers.json file is in the current path where the command is being executed from.

## Additional Items to Note

- Docker `--volume` is used to mount paths to make the input file to load available within the container at `/input`, and an output path on the host to the path `/output`; where the error log and with info response files are written and persisted.
- The number of threads to use is automatically estimated for loading and processing redo records. If the Senzing database is also running on the same machine and you notice very high CPU load, you can reduce the number of threads with the CLI argument `--numThreads` or the `SENZING_THREADS_PER_PROCESS` environment variable. To know how many threads a run started with look for a similar message during startup:

```console
2022-12-08 15:58:39,045 - file-loader - INFO:  Starting to load with 12 threads...
```
- If you have a Senzing license, this can be specified in the JSON configuration with the `LICENSESTRINGBASE64` key.

```console
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
```
