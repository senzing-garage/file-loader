# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
[markdownlint](https://dlaa.me/markdownlint/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.4] - 2024-06-24

### Changed in 1.3.4

- In `Dockerfile`, updated FROM instruction to `senzing/senzingapi-runtime:3.10.3`

## [1.3.3] - 2024-05-30

### Changed in 1.3.3

- Ensure RECORD_ID is a string when an integer isn't quoted in the input JSON

## [1.3.2] - 2024-05-22

### Changed in 1.3.2

- In `Dockerfile`, updated FROM instruction to `senzing/senzingapi-runtime:3.10.1`

## [1.3.1] - 2023-12-19

### Changed in 1.3.1

- Added mins to results output to indicate time period

## [1.3.0] - 2023-12-19

### Changed in 1.3.0

- Improve performance
- If no input file is specified redo processing will still be performed
- Can run standalone outside of Docker
  
## [1.2.3] - 2023-10-02

### Changed in 1.2.3

- In `Dockerfile`, updated FROM instruction to `senzing/senzingapi-tools:3.7.1`

## [1.2.2] - 2023-02-21

### Fixed in 1.2.2

- Remove debug statement

## [1.2.1] - 2023-02-20

### Fixed in 1.2.1

- Fixed draining of threads for Postgres governor condition

## [1.2.0] - 2023-01-26

### Fixed in 1.2.0

- Fixed abend when priming loader or redeor concurrent futures

## [1.1.1] - 2023-01-23

### Changed in 1.1.1

- Improved handling of result returned from Governor
- Improved calling and checking of long running calls

## [1.1.0] - 2023-01-16

### Added to 1.1.0

- Modify calls to redo APIs
- Ensure there are redo records to process
- Fix messages for redo stats

## [1.0.1] - 2022-12-15

### Added to 1.0.1

- Small fixes

## [1.0.0] - 2022-12-14

### Added to 1.0.0

- Initial release
