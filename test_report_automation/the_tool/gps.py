import os
import sqlite3
import cx_Oracle
import json
from dotmap import DotMap
import all_loggers
import sys
from datetime import datetime as dt
from paramiko import SSHClient
from pypsexec.client import Client


"""
'python',
1 => app_name,                  # App name
2 => tool_dir,                  # tool directory to change CW directory
3 => rel_run_logs_folder,       # Relative to tools directory for run logs
4 => rel_artifacts_folder,      # Relative to the tools directory for collecting artifacts
5 => log_file_name,             # log file name for logs
6 => stdout_file,               # output file name to log std output 
7 => stderr_file,               # error file name to log std errors
"""


args = sys.argv

if len(args) < 8:
    print(f'Exception Not Called with Proper parameters {args}')
    raise Exception(f'Not Called with Proper parameters {args}')

app_name = str(args[1]).strip()
tool_dir = str(args[2]).strip()
rel_run_logs_folder = str(args[3]).strip()
rel_artifacts_folder = str(args[4]).strip()
log_file_name = str(args[5]).strip()
stdout_file = str(args[6]).strip()
stderr_file = str(args[7]).strip()


# ToDO Set Logging in GPS


def get_json(str_data):
    try:
        all_loggers.logger_log.info(f'got For Json conversion: \n{str_data}')
        return json.loads(str_data)
    except Exception as _:
        return []


try:

    helper_db_params = DotMap()

    print('1.1: Setting GPS')
    """
    Steps:
    1. Get values From SQL lite
    2. Get values From PLAB DB
        2.1 Values From PLAB_SERVERS_T
        2.1 Values From PLAB_APP_PARAMETERS
    :param app_name: to get Started With, What is the Name of the App for which results are to be sent.
    :return: Return an object which is dot accessible.
    """

    print('1.2: Setting Variables from SQL Lite')

    # Step 1. Read from SQL Lite
    with sqlite3.connect(os.path.join(all_loggers.web_server_dir, 'helper.db')) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM HELPER_VARIABLES')
        for row in cursor.fetchall():
            setattr(helper_db_params, row[0], row[1])  # row: (oracle_db_cs, 'MS_PLAB/MS_PLAB@msstore:1522/db11203')

    all_loggers.logger_log.info(f'''helper db read and got values as \n {helper_db_params}''')

    svn_client = helper_db_params.svn_client
    oracle_client_Path = helper_db_params.oracle_client_Path
    oracle_db_cs = helper_db_params.oracle_db_cs

    # all_monitors = get_json(helper_db_params.all_monitors)
    test_types = get_json(helper_db_params.test_types)

    # Step 2. Read Values From PLAB_SERVERS_T

    global_conn = cx_Oracle.connect(oracle_db_cs)
    global_cursor = global_conn.cursor()

    all_loggers.logger_log.info(f'''connection made to plab db successfully {global_conn}''')

    with cx_Oracle.connect(oracle_db_cs) as conn:
        with conn.cursor() as cursor:

            query_servers_t = '''
            SELECT 
            APP_IP,
            DB_IP, 
            SYSTEMI_PATH, 
            DB_HOME,
            SCHEMA_NAME, 
            SCHEMA_PWD, 
            APP_ORACLE_PWD,
            APP_ROOT_PWD,
            DB_ORACLE_PWD, 
            DB_ROOT_PWD,
            THREADDUMP_FILE_PATH, 
            WINDOWS_IP, 
            APP_FULL_NAME,
            windows_user_name,
            windows_user_pwd 
            FROM PLAB_SERVERS_T
            WHERE APP = :APP'''

            query_format = {'APP': app_name}

            cursor.execute(query_servers_t, query_format)

            row_servers_t = cursor.fetchone()
            all_loggers.logger_log.info(f'''Ran query for servers details for app {row_servers_t}''')

            if len(row_servers_t) == 0:
                print("Exception: Len of row_servers --> PLAB_SERVERS_T Table is 0")
                raise Exception('Len of row_servers --> PLAB_SERVERS_T Table is 0.')

            query_app_params = '''
            SELECT
            EXECUTION_IP,
            EXECUTION_PROJECT_FOLDER,
            EXECUTION_SCENARIO,
            MONITOR_IP,
            MONITOR_PROJECT_LOCATION,
            MONITOR_SCENARIO,
            TEST_RUN_NO,
            TEST_DESCRIPTION,
            RELEASE_NAME,
            ARTIFACTS_FOLDER,
            SVN_ARTIFACT_FOLDER,
            SVN_OP_LOCATION,
            SVN_USER_NAME,
            SVN_PASSWORD,
            TOTAL_USERS,
            CHANGE_HISTORY,
            ORACLE_DB_PORT,
            ORACLE_DB_ID,
            COMPARE_WITH_OLD,
            WPM_MATTERS,
            TEST_TYPE,
            THREAD_DUMP_LOCATION,
            HEAP_DUMP_LOCATION,
            OLD_RUN,
            OLD_TEST_TYPE,
            OLD_RELEASE_NAME,
            TEST_SCOPE,
            CHANGES_MADE,
            TO_MAIL_FILE,
            INSTALLERS_TO_AVOID,
            ADDITIONAL_FILES_APP,
            ADDITIONAL_FILES_DB,
            ADDITIONAL_DIRS_APP,
            ADDITIONAL_DIRS_DB
            FROM PLAB_APP_PARAMETERS WHERE APP = :APP
            '''

            cursor.execute(query_app_params, query_format)
            row_app_params = cursor.fetchone()
            all_loggers.logger_log.info(f'''Ran query for parameters details for app {row_app_params}''')

            if len(row_app_params) == 0:
                print("Exception: Len of row_app_params --> PLAB_APP_PARAMETERS Table is 0")
                raise Exception('Len of row_app_params --> PLAB_APP_PARAMETERS Table is 0.')

            app_IP = row_servers_t[0]
            db_IP = row_servers_t[1]
            SystemI_Path = row_servers_t[2]
            db_home = row_servers_t[3]
            schema_name = row_servers_t[4]
            schema_pwd = row_servers_t[5]
            App_Oracle_PWD = row_servers_t[6]
            App_Root_PWD = row_servers_t[7]
            DB_Oracle_PWD = row_servers_t[8]
            DB_Root_PWD = row_servers_t[9]
            threaddump_file_path = row_servers_t[10]
            execution_IP = row_servers_t[11]
            app_full_name = row_servers_t[12]
            windows_user_name = row_servers_t[13]
            windows_user_pwd = row_servers_t[14]
            user = "oracle"
            pwd = "oracle"

            script_version = 1
            execution_project_folder = row_app_params[1]
            execution_scenario = row_app_params[2]
            monitor_IP = row_app_params[3]
            # monitor_project_location = row_app_params[4]
            # monitor_scenario = row_app_params[5]
            run = str(row_app_params[6])
            run_description = row_app_params[7]
            release_name = row_app_params[8]
            artifacts_folder = row_app_params[9]
            svn_artifact_folder = row_app_params[10]
            svn_op_location = row_app_params[11]
            svn_user_name = row_app_params[12]
            svn_password = row_app_params[13]
            total_users = row_app_params[14]
            change_history = row_app_params[15]
            oracle_db_port = row_app_params[16]
            oracle_db_id = row_app_params[17]
            compare_with_old = row_app_params[18]
            wpm_matters = row_app_params[19]
            test_type = row_app_params[20]
            thread_dump_location = row_app_params[21]
            heap_dump_location = row_app_params[22]
            old_run = row_app_params[23]
            old_test_type = row_app_params[24]
            old_release_name = row_app_params[25]
            test_scope = row_app_params[26].read()
            changes_made = row_app_params[27].read()
            to_mail_file = row_app_params[28].read()
            installers_to_avoid = row_app_params[29].split(',')

            additional_files_app = get_json(row_app_params[30])
            additional_files_db = get_json(row_app_params[31])
            additional_dirs_app = get_json(row_app_params[32])
            additional_dirs_db = get_json(row_app_params[33])

            monitor_available = True if monitor_IP.upper() == 'NA' else False
            compare_with_old = True if bool(compare_with_old) else False
            wpm_matters = True if bool(wpm_matters) else False

            test_scope = get_json(test_scope)
            changes_made = get_json(changes_made)
            to_mail_file = get_json(to_mail_file)

    print('1.3: GPS Setting is done.')

except Exception as e:
    print(f"Exception: {e}")
    raise e


all_loggers.logger_log.info(f'Connecting for RCE: {execution_IP}, {windows_user_name}, {windows_user_pwd}')
rce = Client(execution_IP, username=windows_user_name, password=windows_user_pwd)
rce.connect()
try:
    rce.create_service()

except Exception as e:
    all_loggers.logger_log.info(f'Failed to Create RCE service {e}')
    all_loggers.logger_log.exception(e)
    rce = 'NA'


""" Helper Variables """
pt_results_run_result_sequence = ''
index_from_res_path = ''
latest_folder = ''
number_of_users_in_test = ''
test_start_time = dt.now()
test_stop_time = dt.now()
wpm_required = ''
wpm_achieve = ''
time_diff_bwn_exec_db = ''
db_zone = ''
rampup_time_secs = ''
app_cores = ''
app_ram = ''
app_cpu_util = ''
app_mem_util = ''
db_cores = ''
db_ram = ''
db_cpu_util = ''
db_mem_util = ''
ssh_app = SSHClient()
sftp_app = ''
ssh_db = SSHClient()
sftp_db = ''
test_status = ''

tc_thread_count = ''
logical_blocks = ''

avg_pages_ps = ''
avg_req_s_ps = ''
avg_throughput_ps = ''
avg_txn_rt = ''

mail_api = 'http://msi-aio145:5678/sendmail'


def is_float(number):
    try:
        float(number)
        return True
    except Exception as _:
        return False
