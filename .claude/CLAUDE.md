# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

file-loader is a Python utility to load Senzing mapped JSON data records and process redo records. It's part of the Senzing Garage (experimental projects) and runs as either a Docker container or standalone Python application.

## Build and Development Commands

### Linting

```bash
# Run pylint on all Python files (uses .pylintrc configuration)
pylint $(git ls-files '*.py')
```

### Docker Build

```bash
# Build the Docker image
docker build -t senzing/file-loader .

# Run container tests
docker-compose -f docker-compose.test.yml up --build
```

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the loader (requires SENZING_ENGINE_CONFIGURATION_JSON)
./file-loader.py -f <input_file.json>
```

### Python Version Support

Tested on Python 3.10, 3.11, 3.12, 3.13

## Architecture

### Main Components (file-loader.py)

The application is a single-file Python script with these key functions:

- `load_and_redo()` - Main orchestration function that manages thread pools for loading and redo processing
- `add_record()` - Adds a single JSON record to the Senzing engine
- `get_redo_record()` / `prime_redo_records()` - Fetches redo records for batch resolution
- `process_redo_record()` - Processes redo records for entity resolution
- `startup_info()` - Displays license, version, config, and DB info at startup

### Threading Model

Uses `concurrent.futures.ThreadPoolExecutor` for parallel record processing. Thread count is auto-calculated based on hardware or configurable via `--numThreads` / `SENZING_THREADS_PER_PROCESS`.

### Senzing Engine Integration

Uses Senzing Python SDK modules: `G2Engine`, `G2Diagnostic`, `G2Product`, `G2ConfigMgr`

### PostgreSQL Governor

For PostgreSQL databases, optionally integrates with `senzing_governor` to manage transaction ID (XID) aging and prevent database issues.

### Error Handling

Three-level exception hierarchy:

- `G2BadInputException` - Invalid input data
- `G2RetryableException` - Transient errors that may succeed on retry
- `G2Exception` - General engine errors

### Configuration Precedence

1. CLI arguments (highest priority)
2. Environment variables
3. Default values

Custom argparse actions (`CustomArgActionStoreTrue`, `CustomArgAction`) track whether values came from CLI to implement this precedence.

## Required Environment Variables

- `SENZING_ENGINE_CONFIGURATION_JSON` - JSON string with Senzing engine configuration including database connection

## Optional Environment Variables

- `SENZING_INPUT_FILE` - Path to JSON file to load
- `SENZING_WITHINFO` - Enable detailed "WithInfo" response output
- `SENZING_DEBUG` - Enable debug tracing
- `SENZING_THREADS_PER_PROCESS` - Number of worker threads

## Output Files

When running, the loader may create:

- `file-loader_errors_YYYYMMDD_HHMMSS.log` - Error log file
- `file-loader_withInfo_YYYYMMDD_HHMMSS.jsonl` - WithInfo responses (if enabled)

## Docker Image

Built from `senzing/senzingapi-runtime` base image. Runs as non-root user (UID 1001). Mount data directory to `/data` for input/output files.

## Dependencies

- `orjson` - Fast JSON serialization (falls back to stdlib `json` if unavailable)
- `psycopg2-binary` - PostgreSQL adapter
- Senzing SDK (provided by base image)
