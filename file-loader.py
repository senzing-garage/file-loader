#! /usr/bin/env python3

import argparse
import concurrent.futures
import importlib
import itertools
import logging
import os
import pathlib
import signal
import sys
import textwrap
import time
from datetime import datetime
from senzing import G2BadInputException, G2ConfigMgr, G2Diagnostic, G2Engine, G2Exception, G2Product, \
    G2RetryableException, G2UnrecoverableException
try:
    import orjson as json
except ModuleNotFoundError:
    import json

__all__ = []
__version__ = '1.1.0'  # See https://www.python.org/dev/peps/pep-0396/
__date__ = '2022-11-29'
__updated__ = '2023-01-16'


# Custom actions for argparse. Enables checking if an arg "was specified" on the CLI to check if CLI args should take
# precedence over env vars and still can use the default setting for an arg if neither were specified.
class CustomArgActionStoreTrue(argparse.Action):
    """Set to true like using normal action=store_true and set _specified key for lookup"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)
        setattr(namespace, self.dest+'_specified', True)


class CustomArgAction(argparse.Action):
    """Set to value and set _specified key for lookup"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest+'_specified', True)


def arg_convert_boolean(env_var, cli_arg):
    """Convert boolean env var to True or False if set, otherwise use cli arg value"""
    evar = os.getenv(env_var)
    if evar:
        if isinstance(evar, str):
            if evar.lower() in ['true', '1', 't', 'y', 'yes']:
                return True
            return False

        return evar

    return cli_arg


def startup_info(engine, diag, product, configmgr):
    """Fetch and display information at startup. Detect if Postgres is in use to use Governor"""
    lic_info = json.loads(product.license())
    ver_info = json.loads(product.version())

    try:
        response = bytearray()
        configmgr.getConfigList(response)
        config_list = json.loads(response.decode())

        response = bytearray()
        engine.getActiveConfigID(response)
        active_cfg_id = int(response.decode())

        response = bytearray()
        diag.getDBInfo(response)
        db_info = json.loads(response.decode())
    except G2Exception as ex:
        logger.error(f'Failed to get startup information: {ex}')
        sys.exit(-1)

    # Get details for the currently active ID
    active_cfg_details = [details for details in config_list['CONFIGS'] if details['CONFIG_ID'] == active_cfg_id]
    config_comments = active_cfg_details[0]['CONFIG_COMMENTS']
    config_created = active_cfg_details[0]['SYS_CREATE_DT']

    # Get database information
    db_info_type_name = [(db["Type"], db["Name"]) for db in db_info['Database Details']]
    uniq_db_type = set(info[0].lower() for info in db_info_type_name)

    logger.info('Version & Configuration')
    logger.info('-----------------------')
    logger.info('')
    logger.info(f'Senzing Version:            {ver_info["VERSION"] + " (" + ver_info["BUILD_DATE"] + ")"  if "VERSION" in ver_info else ""}')
    logger.info(f'Instance Config ID:         {active_cfg_id}')
    logger.info(f'Instance Config Comments:   {config_comments}')
    logger.info(f'Instance Config Created:    {config_created}')
    logger.info(f'Hybrid Database:            {"Yes" if db_info["Hybrid Mode"] else "No"}')
    logger.info(f'Database(s):                {db_info_type_name[0][0] + " - " + db_info_type_name[0][1] if len(db_info_type_name) == 1 else ""}')
    if len(db_info_type_name) > 1:
        for type_name in db_info_type_name:
            logger.info(f'{" " * 28}{type_name[0] + " - " + type_name[1]}')

    logger.info('')
    logger.info('License')
    logger.info('-------')
    logger.info('')
    logger.info(f'Customer:    {lic_info["customer"]}')
    logger.info(f'Type:        {lic_info["licenseType"]}')
    logger.info(f'Records:     {lic_info["recordLimit"]}')
    logger.info(f'Expiration:  {lic_info["expireDate"]}')
    logger.info(f'Contract:    {lic_info["contract"]}')
    logger.info('')

    return bool('postgresql' in uniq_db_type)


def add_record(engine, rec_to_add, with_info):
    """Add a single record, returning with info details if --info or SENZING_WITHINFO was specified"""
    record_dict = json.loads(rec_to_add)
    data_source = record_dict.get('DATA_SOURCE', None)
    record_id = record_dict.get('RECORD_ID', None)

    if with_info:
        info_response = bytearray()
        engine.addRecordWithInfo(data_source, record_id, rec_to_add, info_response)
        return info_response.decode()

    engine.addRecord(data_source, record_id, rec_to_add)
    return None


def get_redo_records(engine, quantity):
    """Get a specified number of redo records for processing"""
    redo_records = []
    try:
        for _ in range(quantity):
            redo_record = bytearray()
            engine.getRedoRecord(redo_record)
            redo_records.append(redo_record.decode())
    except G2Exception as ex:
        logger.critical(f'Exception: {ex} - Operation: getRedoRecord')
        global do_shutdown
        do_shutdown = True
        return None

    return redo_records if len(redo_records) > 1 else redo_records[0]


def process_redo_record(engine, record, with_info):
    """Process a single redo record, returning with info details if --info or SENZING_WITHINFO was specified"""
    if with_info:
        with_info_response = bytearray()
        engine.processWithInfo(record, with_info_response)
        return with_info_response.decode()

    engine.process(record)
    return None


def record_stats(success_recs, error_recs, prev_time, operation):
    """Log details on records for add/redo"""
    logger.info(f'Processed {success_recs:,} {operation}, {int(1000 / (time.time() - prev_time)):,} records per second, {error_recs} errors')
    return time.time()


def workload_stats(engine):
    """Log engine workload stats"""
    response = bytearray()
    try:
        engine.stats(response)
        logger.info('')
        logger.info(f'{response.decode()}')
        logger.info('')
    except G2Exception as ex:
        logger.critical(f'Exception: {ex} - Operation: stats')
        global do_shutdown
        do_shutdown = True


def long_running_check(futures, time_now, num_workers):
    """Check for long-running records"""
    num_stuck = 0
    for fut, payload in futures.items():
        if not fut.done():
            duration = time_now - payload[PAYLOAD_START_TIME]
            if duration > LONG_RECORD:
                num_stuck += 1
                stuck_record = json.loads(payload[PAYLOAD_RECORD])
                logger.warning(f'Long running record ({duration / 60:.3g}): {stuck_record["DATA_SOURCE"]} - {stuck_record["RECORD_ID"]}')

    if num_stuck >= num_workers:
        logger.warning(f'All {num_workers} threads are stuck processing long running records')


def check_governor():
    """Check Postgres XID and slow down load if required"""
    gov_pause_secs = gov.govern()
    if gov_pause_secs > 0:
        logger.info(f'Pausing for {gov_pause_secs} secs, governor has triggered for Postgres database(s)... ')
        time.sleep(gov_pause_secs)


def signal_int(signum, frame):
    """Catch interrupt to allow running threads to finish"""
    logger.warning('Please wait for running tasks to complete, this could take many minutes...\n')
    global do_shutdown
    do_shutdown = True


def load_and_redo(engine, file_input, file_output, file_errors, num_workers, with_info, call_governor):
    """Load records and process redo records after loading is complete"""
    global do_shutdown
    prev_time = time.time()
    success_recs = error_recs = redo_error_recs = redo_success_recs = 0
    start_time = time.time()

    with open(file_output, 'w') as out_file:
        with open(file_input, 'r') as in_file:
            load_records = 0
            long_check_time = time.time()

            # Loader
            with concurrent.futures.ThreadPoolExecutor(num_workers if num_workers else None) as loader:
                futures = {loader.submit(add_record, engine, record, with_info): (record.strip(), time.time()) for record in itertools.islice(in_file, loader._max_workers)}
                logger.info(f'Starting to load with {loader._max_workers} threads...')
                load_records += loader._max_workers

                while futures:
                    time_now = time.time()

                    if call_governor:
                        check_governor()

                    for f in concurrent.futures.as_completed(futures.keys()):
                        try:
                            result = f.result()
                        except (G2BadInputException, G2RetryableException, json.JSONDecodeError) as ex:
                            logger.error(f'Exception: {ex} - Operation: addRecord - Record: {futures[f][PAYLOAD_RECORD]}')
                            error_recs += 1
                        except (G2Exception, G2UnrecoverableException) as ex:
                            logger.critical(f'Exception: {ex} - Operation: addRecord - Record: {futures[f][PAYLOAD_RECORD]}')
                            do_shutdown = True
                        else:
                            record = in_file.readline()
                            if record and not do_shutdown:
                                load_records += 1
                                futures[loader.submit(add_record, engine, record.strip(), with_info)] = (record.strip(), time.time())

                            success_recs += 1
                            if success_recs % 1000 == 0:
                                prev_time = record_stats(success_recs, error_recs, prev_time, 'adds')

                            if success_recs % 10000 == 0:
                                workload_stats(engine)

                            if result:
                                out_file.write(result + '\n')

                            if time_now > long_check_time + (LONG_RECORD / 2):
                                long_check_time = time_now
                                long_running_check(futures, time_now, loader._max_workers)
                        finally:
                            futures.pop(f)

            logger.info(f'Successfully loaded {success_recs} records, with {error_recs} errors')

            # If interrupted during load don't perform redo
            if do_shutdown:
                logger.warning('Processing was interrupted, shutting down. Loading may not be complete and redo processing will not be started.')
                sys.exit(-1)

            # Redoer
            logger.info('Checking for and processing redo records...')
            redo_records = 0
            redo_count = engine.countRedoRecords()

            if redo_count:
                long_check_time = time.time()
                with concurrent.futures.ThreadPoolExecutor(num_workers if num_workers else None) as redoer:
                    futures = {redoer.submit(process_redo_record, engine, record, with_info): (record, time.time()) for record in get_redo_records(engine, redoer._max_workers)}
                    logger.info(f'Starting to process redo with {redoer._max_workers} threads...')
                    redo_records += redoer._max_workers
                    while futures:
                        time_now = time.time()

                        if call_governor:
                            check_governor()

                        for f in concurrent.futures.as_completed(futures.keys()):
                            try:
                                result = f.result()
                                redo_record = get_redo_records(engine, 1)
                            except (G2BadInputException, G2RetryableException, json.JSONDecodeError) as ex:
                                logger.error(f'Exception: {ex} - Operation: getRedoRecord - Record: {futures[f][PAYLOAD_RECORD]}')
                                redo_error_recs += 1
                            except (G2Exception, G2UnrecoverableException) as ex:
                                logger.critical(f'Exception: {ex} - Operation: getRedoRecord - Record: {futures[f][PAYLOAD_RECORD]}')
                                do_shutdown = True
                            else:
                                if redo_record and not do_shutdown:
                                    redo_records += 1
                                    futures[redoer.submit(process_redo_record, engine, redo_record, with_info)] = (redo_record, time.time())

                                redo_success_recs += 1
                                if redo_success_recs % 1000 == 0:
                                    prev_time = record_stats(redo_success_recs, redo_error_recs, prev_time, 'redo')

                                if redo_success_recs % 10000 == 0:
                                    workload_stats(engine)

                                if result:
                                    out_file.write(result + '\n')

                                if time_now > long_check_time + (LONG_RECORD / 2):
                                    long_check_time = time_now
                                    long_running_check(futures, time_now, redoer._max_workers)
                            finally:
                                futures.pop(f)
            else:
                logger.info('No redo records to process.')

            # If interrupted during redo log details
            if do_shutdown:
                logger.warning('Processing was interrupted, shutting down. Redo may not be complete.')

            logger.info('')
            logger.info('Results')
            logger.info('-------')
            logger.info('')
            logger.info(f'Source File:                     {pathlib.Path(file_input).resolve()}')
            logger.info(f'Total / successful load records: {load_records:,} / {success_recs:,}')
            logger.info(f'Total / successful redo records: {redo_records:,} / {redo_success_recs:,}')
            logger.info(f'Elapsed time:                    {round((time.time() - start_time) / 60, 1)} mins')
            logger.info(f'With Info:                       {file_output if with_info else "Not requested"}')
            logger.info(f'Errors:                          {error_recs:,}{" - " + errors_file if error_recs else ""}')

            # If with info wasn't requested delete the with info output file
            if not cli_args.info and not os.getenv("SENZING_WITHINFO"):
                pathlib.Path(file_output).unlink(missing_ok=True)

            if not error_recs:
                pathlib.Path(file_errors).unlink(missing_ok=True)


if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal_int)
    signal.signal(signal.SIGTERM, signal_int)

    LONG_RECORD = 300
    PAYLOAD_RECORD = 0
    PAYLOAD_START_TIME = 1
    do_shutdown = False
    module_name = pathlib.Path(sys.argv[0]).stem

    szload_parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description='Utility to load Senzing JSON records and process redo records',
        epilog=textwrap.dedent('''\
                 Arguments can be specified with either CLI arguments or environment variables, some arguments have 
                 default values.
        
                 The order of precedence for selecting which value to use is:
        
                   1) CLI Argument
                   2) Environment variable
                   3) Default value if available
                   
                 For additional help and information: https://github.com/Senzing/file-loader/blob/main/README.md
        
               '''),
        formatter_class=argparse.RawTextHelpFormatter)

    szload_parser.add_argument(
        '-f', '--file',
        action=CustomArgAction,
        default=None,
        metavar='file',
        nargs='?',
        help=textwrap.dedent('''\
               Path and name of file to load.
               
               Default: None, must be specified.
               Env Var: SENZING_INPUT_FILE
        
             '''))
    szload_parser.add_argument(
        '-cj', '--configJson',
        action=CustomArgAction,
        default=None,
        metavar='config',
        nargs='?',
        type=str,
        help=textwrap.dedent('''\
               JSON string of the Senzing engine configuration.
               
               Default: None, must be specified.
               Env Var: SENZING_ENGINE_CONFIGURATION_JSON
        
             '''))
    szload_parser.add_argument(
        '-i', '--info',
        action=CustomArgActionStoreTrue,
        default=False,
        nargs=0,
        help=textwrap.dedent('''\
               Produce withInfo messages and write to a file
               
               Default: False
               Env Var: SENZING_WITHINFO
               
             '''))
    szload_parser.add_argument(
        '-t', '--debugTrace',
        action=CustomArgActionStoreTrue,
        default=False,
        nargs=0,
        help=textwrap.dedent('''\
               Output debug trace information.
               
               Default: False
               Env Var: SENZING_DEBUG
    
             '''))
    szload_parser.add_argument(
        '-nt', '--numThreads',
        action=CustomArgAction,
        default=0,
        metavar='num_threads',
        type=int,
        help=textwrap.dedent('''\
               Total number of worker threads performing load.
    
               Default: Calculated based on hardware.
               Env Var: SENZING_THREADS_PER_PROCESS
    
             '''))

    cli_args = szload_parser.parse_args()

    # If a CLI arg was specified use it, else try the env var, if no env var use the default for the CLI arg
    # Sets the priority to 1) CLI arg, 2) Env Var 3) Default value
    ingest_file = cli_args.file if cli_args.__dict__.get('file_specified') else os.getenv("SENZING_INPUT_FILE")
    engine_config = cli_args.configJson if cli_args.__dict__.get('configJson_specified') else os.getenv("SENZING_ENGINE_CONFIGURATION_JSON", cli_args.configJson)
    withinfo = cli_args.info if cli_args.__dict__.get('info_specified') else arg_convert_boolean("SENZING_WITHINFO", cli_args.info)
    debug_trace = cli_args.debugTrace if cli_args.__dict__.get('debugTrace_specified') else arg_convert_boolean("SENZING_DEBUG", cli_args.debugTrace)
    num_threads = cli_args.numThreads if cli_args.__dict__.get('numThreads_specified') else int(os.getenv("SENZING_THREADS_PER_PROCESS", cli_args.numThreads))

    withinfo_file = f'/output/{module_name}_withInfo_{str(datetime.now().strftime("%Y%m%d_%H%M%S"))}.jsonl'
    errors_file = f'/output/{module_name}_errors_{str(datetime.now().strftime("%Y%m%d_%H%M%S"))}.log'

    # Create logger
    try:
        logger = logging.getLogger(sys.argv[0].rstrip('.py').lstrip('./'))
        console_handle = logging.StreamHandler(stream=sys.stdout)
        console_handle.setLevel(logging.INFO)
        file_handle = logging.FileHandler(errors_file, 'w')
        file_handle.setLevel(logging.ERROR)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        log_format = '%(asctime)s - %(name)s - %(levelname)s:  %(message)s'
        console_handle.setFormatter(logging.Formatter(log_format))
        file_handle.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console_handle)
        logger.addHandler(file_handle)
    except IOError as ex:
        print(ex)
        print('\nBoth /input and /output must be mounted to the host system.')
        print(f'Example: docker run -it --rm -u $UID -v ${{PWD}}:/input -v ${{PWD}}:/output -e SENZING_ENGINE_CONFIGURATION_JSON  senzing/{module_name} -f /input/load_file.json')
        sys.exit(-1)

    if not ingest_file:
        logger.warning('An input file to load must be specified with --file or SENZING_INPUT_FILE environment variable')
        sys.exit(-1)

    if not engine_config:
        logger.warning('SENZING_ENGINE_CONFIGURATION_JSON environment variable or --configJson CLI argument must be set with the engine configuration JSON')
        logger.warning('https://senzing.zendesk.com/hc/en-us/articles/360038774134-G2Module-Configuration-and-the-Senzing-API')
        sys.exit(-1)

    try:
        sz_engine = G2Engine()
        sz_engine.init('G2Engine', engine_config, debug_trace)

        sz_diag = G2Diagnostic()
        sz_diag.init('G2Diagnostic', engine_config, debug_trace)

        sz_product = G2Product()
        sz_product.init('G2Product', engine_config, debug_trace)

        sz_configmgr = G2ConfigMgr()
        sz_configmgr.init('pyG2ConfigMgr', engine_config, debug_trace)
    except G2Exception as ex:
        logger.error(ex)
        sys.exit(-1)

    # If the database is Postgres import the governor
    db_is_postgres = startup_info(sz_engine, sz_diag, sz_product, sz_configmgr)
    if db_is_postgres:
        logger.info('Postgres detected, loading the Senzing governor')
        logger.info('')
        senzing_governor = importlib.import_module("senzing_governor")
        gov = senzing_governor.Governor(hint="SzLoader")

    load_and_redo(sz_engine, ingest_file, withinfo_file, errors_file, num_threads, withinfo, db_is_postgres)

    try:
        sz_diag.destroy()
        sz_product.destroy()
        sz_configmgr.destroy()
        sz_engine.destroy()
    except G2Exception as ex:
        logger.error(ex)
