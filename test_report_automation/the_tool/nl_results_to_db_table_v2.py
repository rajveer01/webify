import datetime
import json
import all_loggers
import unicodedata as ucd

import pandas as pd

import gps
import nl_txn_name_finder


def push_records(transactions_html):
    try:
        all_loggers.logger_log.info(f'entered to push records() function with txn file: {transactions_html}')
        tables = pd.read_html(transactions_html)

        time_stamp = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
        date_and_time = datetime.datetime.now().strftime("%Y/%m/%d/%H_%M_%S")

        gps.global_cursor.execute('select PT_RESULTS_RUN_RESULT_SEQUENCE.nextval from dual')
        gps.pt_results_run_result_sequence = int(gps.global_cursor.fetchone()[0])

        sql = '''
            INSERT INTO PT_RESULTS (TIME_STAMP, ROW_ID, DATE_N_TIME, RELEASE_NAME, APP_NAME,
            TEST_RUN_NO,TEST_DESCRIPTION, SCENARIO_NAME, OP_TRANSACTION_NAME, 
            NL_TRANSACTION_NAME, EXPECTED_WPM, EXPECTED_RESPONSE_TIME, RESULT_MIN,
            RESULT_AVG, RESULT_MAX, RESULT_COUNT, RESULT_ERROR_PERC, 
            RESULT_90_PERC, SCRIPT_VERSION, TEST_START_DATE, TEST_TYPE, PT_RESULTS_RUN_RESULT_ROW_ID) 
            VALUES (
            :timestamp, PT_Row_ID_sequence.nextval, TO_DATE(:date_and_time, 'yyyy/mm/dd hh24_mi_ss'), 
            :Release_Name, :App_Name, :Test_Run_No, :Test_Description, :scenario_name, 
            :op_transaction_name, :NL_Transaction_name, :expected_wpm, 
            :expected_response_time, :result_min, :result_avg, :result_max, :result_count, 
            :result_error_perc, :result_90_perc, :SCRIPT_VERSION, :TEST_START_DATE, 
            :TEST_TYPE, :PT_RESULTS_RUN_RESULT_ROW_ID)
            '''
        txn_description_dict = nl_txn_name_finder.get_dict()

        all_loggers.logger_log.info(f'''Got all_ the transactions as dictionary. Trying to read html of transactions as:
         {txn_description_dict}''')

        for df in tables:
            no_rows_in_df = df.shape[0]
            for i in range(no_rows_in_df):
                nl_txn_name = tuple(df[i:i + 1].get('Unnamed: 0'))[0]
                result_min = tuple(df[i:i + 1].get('Min'))[0] if gps.is_float(tuple(df[i:i + 1].get('Min'))[0]) else 0
                result_avg = tuple(df[i:i + 1].get('Avg'))[0] if gps.is_float(tuple(df[i:i + 1].get('Avg'))[0]) else 0
                result_max = tuple(df[i:i + 1].get('Max'))[0] if gps.is_float(tuple(df[i:i + 1].get('Max'))[0]) else 0
                result_count = tuple(df[i:i + 1].get('Count'))[0] if gps.is_float(
                    tuple(df[i:i + 1].get('Count'))[0]) else 0
                result_error_perc = tuple(df[i:i + 1].get('% of Err'))[0] if gps.is_float(
                    tuple(df[i:i + 1].get('% of Err'))[0]) else 0
                result_90_perc = tuple(df[i:i + 1].get('Perc 90'))[0] if gps.is_float(
                    tuple(df[i:i + 1].get('Perc 90'))[0]) else 0

                result_min = round(float(result_min), 3)
                result_avg = round(float(result_avg), 3)
                result_max = round(float(result_max), 3)
                result_count = round(float(result_count), 3)
                result_error_perc = round(float(result_error_perc), 3)
                result_90_perc = round(float(result_90_perc), 3)

                if nl_txn_name not in txn_description_dict:
                    all_loggers.logger_log.info(f'Continued and skipped the {nl_txn_name}')
                    continue

                json_for_txn = json.loads(txn_description_dict[nl_txn_name])
                scenario_name = json_for_txn['scenario']
                expected_wpm = json_for_txn['wpm']
                op_transaction_name = str(json_for_txn['op_txn_name']).encode('ascii', 'ignore').decode()
                expected_response_time = json_for_txn['expected_response_time']

                format_sql = {'timestamp': time_stamp, 'date_and_time': date_and_time, 'Release_Name': gps.release_name,
                              'App_Name': gps.app_name, 'Test_Run_No': gps.run, 'Test_Description': gps.run_description,
                              'scenario_name': scenario_name,
                              'op_transaction_name': op_transaction_name.encode('ascii', 'ignore').decode(),
                              'NL_Transaction_name': ucd.normalize('NFKD', nl_txn_name).encode('ascii',
                                                                                               'ignore').decode(),
                              'expected_wpm': expected_wpm,
                              'expected_response_time': expected_response_time, 'result_min': result_min,
                              'result_avg': result_avg, 'result_max': result_max, 'result_count': result_count,
                              'result_error_perc': result_error_perc, 'result_90_perc': result_90_perc,
                              'SCRIPT_VERSION': gps.script_version, 'TEST_START_DATE': gps.test_start_time,
                              'TEST_TYPE': gps.test_type,
                              'PT_RESULTS_RUN_RESULT_ROW_ID': gps.pt_results_run_result_sequence
                              }
                all_loggers.logger_log.info(f'Executing the sql with below data binding. {format_sql}')
                gps.global_cursor.execute(sql, format_sql)
        all_loggers.logger_log.info('res to Table is done')

    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
