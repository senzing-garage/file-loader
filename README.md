 # file-loader
 
 ## Synopsis

Load JSON records from a file into Senzing and process redo records.

 ## Overview

file-loader.py is a Python utility to load [Senzing mapped JSON data](https://senzing.zendesk.com/hc/en-us/articles/231925448-Generic-Entity-Specification), once loading is complete [redo records](https://senzing.zendesk.com/hc/en-us/articles/360007475133-Processing-REDO) are processed. file-loader.py can be run stand alone on a [bare metal Senzing installation](https://senzing.zendesk.com/hc/en-us/articles/115002408867-Quickstart-Guide) or utilized as a Docker container. 

To see command line and environment variable arguments, run:

```console
$ ./file-loader.py --help
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

## Preamble

At [Senzing](http://senzing.com),
we strive to create GitHub documentation in a
"[don't make me think](https://github.com/Senzing/knowledge-base/blob/main/WHATIS/dont-make-me-think.md)" style.
For the most part, instructions are copy and paste.
Whenever thinking is needed, it's marked with a "thinking" icon :thinking:.
Whenever customization is needed, it's marked with a "pencil" icon :pencil2:.
If the instructions are not clear, please let us know by opening a new
[Documentation issue](https://github.com/Senzing/template-python/issues/new?template=documentation_request.md)
describing where we can improve.   Now on with the show...

### Legend

1. :thinking: - A "thinker" icon means that a little extra thinking may be required.
   Perhaps there are some choices to be made.
   Perhaps it's an optional step.
1. :pencil2: - A "pencil" icon means that the instructions may need modification before performing.
1. :warning: - A "warning" icon means that something tricky is happening, so pay attention.

## Contents

1. [Preamble](#preamble)
    1. [Legend](#legend)
1. [Senzing Engine Configuration](#senzing-engine-configuration) 
    1. [Senzing APIs Bare Metal Configuration](#senzing-apis-bare-metal-configuration)
    1. [Docker Configuration](#docker-configuration)
1. [Examples](#examples)
    1. [Senzing APIs Bare Metal](#senzing-apis-bare-metal)
    1. [Docker](#docker)
1. [Build Docker Image](#build-docker-image)
1. [Docker Volumes](#docker-volumes)
1. [Number of Threads](#number-of-threads)
1. [Arguments Order of Precedence](#arguments-order-of-precedence)
1. [License](#license)

## Senzing Engine Configuration

A JSON configuration string is used to specify initialization parameters to the Senzing engine:

```json
{
    "PIPELINE":
    {
        "SUPPORTPATH": "/home/senzing/mysenzproj1/data",
        "CONFIGPATH": "/home/senzing/mysenzproj1/etc",
        "RESOURCEPATH": "/home/senzing/mysenzproj1/resources"
    },
    "SQL":
    {
        "CONNECTION": "postgresql://user:password@host:5432:g2"
    }
}
```

The JSON configuration string - along with other arguments - can be provided via either a CLI argument (`--configJson`) or an environment variable (`SENZING_ENGINE_CONFIGURATION_JSON`).

### Senzing APIs Bare Metal Configuration

You may already have installed the Senzing APIs on a machine and created a Senzing project by following the [Quickstart Guide](https://senzing.zendesk.com/hc/en-us/articles/115002408867-Quickstart-Guide). If not, and you would like to install the Senzing APIs directly on a machine, follow the steps in the[ Quickstart Guide](https://senzing.zendesk.com/hc/en-us/articles/115002408867-Quickstart-Guide). Be sure to review the API [Quickstart Roadmap](https://senzing.zendesk.com/hc/en-us/articles/115001579954-API-Quickstart-Roadmap), especially the [System Requirements](https://senzing.zendesk.com/hc/en-us/articles/115010259947).

When using a bare metal install, the initialization parameters used by the Senzing Python utilities are maintained within <project_path>/etc/G2Module.ini.

🤔To convert an existing Senzing project G2Module.ini file to a JSON string use one of the following methods:
* [SenzingGo.py](https://github.com/Senzing/senzinggo)
    * ```console
      <project_path>/python/SenzingGo.py --iniToJson
      ```
* [jc](https://github.com/kellyjonbrazil/jc)
    * ```console
      cat <project_path>/etc/G2Module.ini | jc --ini
      ```
* Python one liner
    * ```python
      python3 -c $'import configparser; ini_file_name = "<project_path>/etc/G2Module.ini";engine_config_json = {};cfgp = configparser.ConfigParser();cfgp.optionxform = str;cfgp.read(ini_file_name)\nfor section in cfgp.sections(): engine_config_json[section] = dict(cfgp.items(section))\nprint(engine_config_json)'
      ```
✏️Modify `<project_path>` to point to your project

### Docker Configuration

The included Dockerfile leverages the [Senzing API runtime](https://github.com/Senzing/senzingapi-runtime) image. When using as a container the JSON configuration is relative to the paths within the container.  The JSON configuration should look like:

```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "postgresql://senzing:password@myhost:5432:g2"
  }
}
```

✏️You only need to modify the `CONNECTION` string to point to your Senzing database.


## Examples
### Senzing APIs Bare Metal 

#### CLI Arguments

Minimum arguments to load file. 

```console
./file-loader.py \
   --configJson '{"PIPELINE": {"SUPPORTPATH": "/home/senzing/mysenzproj1/data", "CONFIGPATH": "/home/senzing/mysenzproj1/etc", "RESOURCEPATH": "/home/senzing/mysenzproj1/resources"}, "SQL": {"CONNECTION": "postgresql://postgres:password@host:5432:g2"}}' \
   --file /home/senzing/data/load-file.json
```

Load file and write with info responses to a specific file.

```console
./file-loader.py \
   --configJson '{"PIPELINE": {"SUPPORTPATH": "/home/senzing/mysenzproj1/data", "CONFIGPATH": "/home/senzing/mysenzproj1/etc", "RESOURCEPATH": "/home/senzing/mysenzproj1/resources"}, "SQL": {"CONNECTION": "postgresql://postgres:password@host:5432:g2"}}' \
   --file /home/senzing/data/load-file.json \
   --info \
   --infoFile /home/senzing/data/WithInfo.jsonl
```

#### Environment Variables

Minimum variables to load file. 

```console
export SENZING_ENGINE_CONFIGURATION_JSON='{"PIPELINE": {"SUPPORTPATH": "/home/senzing/mysenzproj1/data", "CONFIGPATH": "/home/senzing/mysenzproj1/etc", "RESOURCEPATH": "/home/senzing/mysenzproj1/resources"}, "SQL": {"CONNECTION": "postgresql://postgres:password@host:5432:g2"}}'
export SENZING_INPUT_FILE=/home/senzing/data/load-file.json
./file-loader.py
```

Load file and write with info responses to a specific file.

```console
export SENZING_ENGINE_CONFIGURATION_JSON='{"PIPELINE": {"SUPPORTPATH": "/home/senzing/mysenzproj1/data", "CONFIGPATH": "/home/senzing/mysenzproj1/etc", "RESOURCEPATH": "/home/senzing/mysenzproj1/resources"}, "SQL": {"CONNECTION": "postgresql://postgres:password@host:5432:g2"}}'
export SENZING_INPUT_FILE=/home/senzing/data/load-file.json
export SENZING_WITHINFO=1
export SENZING_WITHINFO_FILE=/home/senzing/data/WithInfo.jsonl
./file-loader.py
```

### Docker

#### CLI Arguments

Minimum arguments to load file. 

```console
docker run \
  --interactive \
  --rm \
  --user $UID \
  --volume /home/senzing/data:/input \
  --volume /home/senzing/data/output:/output \
  senzing/file-loader \
    --configJson '{"CONFIGPATH":"/etc/opt/senzing","RESOURCEPATH":"/opt/senzing/g2/resources","SUPPORTPATH":"/opt/senzing/data"},"SQL":{"CONNECTION":"postgresql://senzing:password@host:5432:g2"}}' \
    --file /input/load-file.json
```
Load file and write with info responses to a file.

```console
docker run \
  --interactive \
  --rm \
  --user $UID \
  --volume /home/senzing/data:/input \
  --volume /home/senzing/data/output:/output \
  senzing/file-loader \
    --configJson '{"CONFIGPATH":"/etc/opt/senzing","RESOURCEPATH":"/opt/senzing/g2/resources","SUPPORTPATH":"/opt/senzing/data"},"SQL":{"CONNECTION":"postgresql://senzing:password@host:5432:g2"}}' \
    --file /input/load-file.json \
    --info
```

#### Environment Variables

Minimum variables to load file. 

```console
export SENZING_ENGINE_CONFIGURATION_JSON='{"CONFIGPATH":"/etc/opt/senzing","RESOURCEPATH":"/opt/senzing/g2/resources","SUPPORTPATH":"/opt/senzing/data"},"SQL":{"CONNECTION":"postgresql://senzing:password@host:5432:g2"}}'
export SENZING_INPUT_FILE=/input/load-file.json
docker run \
  --env SENZING_ENGINE_CONFIGURATION_JSON \
  --env SENZING_INPUT_FILE \
  --interactive \
  --rm \
  --user $UID \
  --volume /home/senzing/data:/input \
  --volume /home/senzing/data/output:/output \
  senzing/file-loader
```

Load file and write with info responses to a file.

```console
export SENZING_ENGINE_CONFIGURATION_JSON='{"CONFIGPATH":"/etc/opt/senzing","RESOURCEPATH":"/opt/senzing/g2/resources","SUPPORTPATH":"/opt/senzing/data"},"SQL":{"CONNECTION":"postgresql://senzing:password@host:5432:g2"}}'
export SENZING_INPUT_FILE=/input/load-file.json
export SENZING_WITHINFO=1
docker run \
  --env SENZING_ENGINE_CONFIGURATION_JSON \
  --env SENZING_INPUT_FILE \
  --env SENZING_WITHINFO \
  --interactive \
  --rm \
  --user $UID \
  --volume /home/senzing/data:/input \
  --volume /home/senzing/data/output:/output \
  senzing/file-loader
```

## Build Docker Image
First clone this repository, then:
```console
cd <repository_dir>
docker build --tag senzing/file-loader .

```

## Docker Volumes 
In the Docker examples `--volume` is used to mount paths to make the input file to load available within the container at `/input`, and an output path on the host to the path `/output`; where the error log and with info response files are written and persisted. You can mount both the input and output to the same host path or seperately.


## Number of Threads
The number of threads to use is automatically estimated for loading and processing redo records. If the Senzing database is also running on the same machine and you notice very high CPU load, you can reduce the number of threads with the CLI argument `--numThreads` or the `SENZING_THREADS_PER_PROCESS` environment variable. To know how many threads a run started with look for a similar message during startup:

```console
2022-12-08 15:58:39,045 - file-loader - INFO:  Starting to load with 12 threads...
```

## Arguments Order of Precedence

CLI arguments or environment variables can be used as arguments, some arguments have default values if not specified. The order or precedence for use is:

1) CLI Argument
2) Environment variable
3) Default value if available

## Senzing Engine License
If you have a Senzing license, this can be specified in the JSON configuration with the `LICENSESTRINGBASE64` key. The value of this is provided in your Senzing license package. 

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

## License

View
[license information](https://senzing.com/end-user-license-agreement/)
for the software container in this Docker image.
Note that this license does not permit further distribution.

This Docker image may also contain software from the
[Senzing GitHub community](https://github.com/Senzing/)
under the
[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

Further, as with all Docker images,
this likely also contains other software which may be under other licenses
(such as Bash, etc. from the base distribution,
along with any direct or indirect dependencies of the primary software being contained).

As for any pre-built image usage,
it is the image user's responsibility to ensure that any use of this image complies
with any relevant licenses for all software contained within.
