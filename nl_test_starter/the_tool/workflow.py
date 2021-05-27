import os
import time
import xml.etree.ElementTree as Et
import zipfile
from datetime import datetime as dt
from glob import glob
import subprocess
import cx_Oracle
import paramiko
import requests
from dotmap import DotMap
from paramiko import SSHClient
from pypsexec.client import Client
from config_tool import main_workflow as config_tool_workflow
import remote_drive_mounter
import json
import all_loggers
import sys

"""
'python',
1 => app_name,                  # App name
2 => tool_dir,                  # tool directory to change CW directory
3 => rel_run_logs_folder,       # Relative to tools directory for run logs
4 => json_file_name,            # Json File for Parameters under the folder Run Logs
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
json_file_name = str(args[4]).strip()
log_file_name = str(args[5]).strip()
stdout_file = str(args[6]).strip()
stderr_file = str(args[7]).strip()

# 0. Setting up variables
print()

# class AppParams:
#     APP: str
#     APP_IP: str
#     DB_IP: str
#     SYSTEMI_PATH: str
#     DB_HOME: str
#     SCHEMA_NAME: str
#     SCHEMA_PWD: str
#     APP_ORACLE_PWD: str
#     APP_ROOT_PWD: str
#     DB_ORACLE_PWD: str
#     DB_ROOT_PWD: str
#     THREADDUMP_FILE_PATH: str
#     WINDOWS_IP: str
#     ACTIVATION_FOR_THIS_RELEASE: str
#     JDK_PATH: str
#     APP_FULL_NAME: str
#     WINDOWS_USER_NAME: str
#     WINDOWS_USER_PWD: str
#     NL_BIN_DIR: str
#     NL_LICENSE_ID: str
#     EXECUTION_IP: str
#     EXECUTION_PROJECT_FOLDER: str
#     EXECUTION_SCENARIO: str
#     MONITOR_IP: str
#     MONITOR_PROJECT_LOCATION: str
#     MONITOR_SCENARIO: str
#     TEST_RUN_NO: int
#     TEST_DESCRIPTION: str
#     RELEASE_NAME: str
#     ARTIFACTS_FOLDER: str
#     SVN_ARTIFACT_FOLDER: str
#     SVN_OP_LOCATION: str
#     SVN_USER_NAME: str
#     SVN_PASSWORD: str
#     TOTAL_USERS: int
#     CHANGE_HISTORY: str
#     ORACLE_DB_PORT: int
#     ORACLE_DB_ID: str
#     COMPARE_WITH_OLD: int
#     WPM_MATTERS: int
#     TEST_TYPE: str
#     THREAD_DUMP_LOCATION: str
#     HEAP_DUMP_LOCATION: str
#     OLD_RUN: int
#     OLD_TEST_TYPE: str
#     OLD_RELEASE_NAME: str
#     TEST_SCOPE: str
#     CHANGES_MADE: str
#     TO_MAIL_FILE: str
#     INSTALLERS_TO_AVOID: str
#     NL_LICENSE_LEASE_H: int
#     NTS: str
#     NTS_LOGIN: str
#     NL_LICENSE_ID: str
#
#     def __init__(self, APP: str):
#         pass
#
# app_params = AppParams(**{})

# class Params:
#     CLEAR_LOGS: bool
#     STOP_APP_SERVICES: bool
#     CONFIG_TOOL: bool
#     START_APP_SERVICES: bool
#     LOAD_NEOLOAD_PROJECT: bool
#     START_TEST: bool
#     TAKE_THREADDUMP: bool
# params = Params()

ssh_app = SSHClient()
rce = ''
ssh_db_ora = SSHClient()
# ssh_db_root = SSHClient()

try:
    with open(os.path.join(rel_run_logs_folder, json_file_name), 'r') as f:
        tool_selection = DotMap(json.loads(f.read()))

    print(json.dumps(tool_selection, indent=2))
    all_loggers.logger_log.info(json.dumps(tool_selection, indent=2))

    BASE_URL = 'http://127.0.0.1:8266'

    headers = {"Content-type": "application/json"}
    with requests.post(f'{BASE_URL}/apis/get_test_params/', data=json.dumps({'app_name': app_name}),
                       headers=headers) as resp:
        if resp.status_code != 200:
            raise Exception(f'Unable to get the Params from API, {resp.status_code} \n {resp.text}')
        app_params = DotMap(resp.json())

    print(f'got app_params as {json.dumps(app_params, indent=2)}')
    all_loggers.logger_log.info(f'got app_params as {json.dumps(app_params, indent=2)}')
    app_params.BASE_URL = BASE_URL


    def ssh_command(ssh_conn: SSHClient, cmd, sync: bool = True):
        all_loggers.logger_log.info(f'got for exec: \n {cmd}')
        inp, out, err = ssh_conn.exec_command(cmd)
        if sync:
            out.channel.recv_exit_status()
        return inp, out, err


    url_project_status = f"http://{app_params.EXECUTION_IP}:7400/Runtime/v1/Service.svc/GetStatus"
    url_project_status_d = f"http://{app_params.EXECUTION_IP}:7400/Design/v1/Service.svc/GetStatus"
    url_is_project_open = f"http://{app_params.EXECUTION_IP}:7400/Design/v1/Service.svc/IsProjectOpen"
    url_project_open = f"http://{app_params.EXECUTION_IP}:7400/Design/v1/Service.svc/OpenProject"
    url_close_project = f"http://{app_params.EXECUTION_IP}:7400/Design/v1/Service.svc/CloseProject"
    url_start_test = f"http://{app_params.EXECUTION_IP}:7400/Runtime/v1/Service.svc/StartTest"
    _____ = '\t'
    nl = "\n"

    ssh_app.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_app.connect(app_params.APP_IP, port=22, username='oracle', password=app_params.APP_ORACLE_PWD)

    print(f'ssh App Connected with {app_params.APP_IP}:22@oracle/{app_params.APP_ORACLE_PWD}')
    all_loggers.logger_log.info(f'ssh App Connected with {app_params.APP_IP}:22@oracle/{app_params.APP_ORACLE_PWD}')
    # ssh_db_ora.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh_db_ora.connect(app_params.DB_IP, port=22, username='oracle', password=app_params.DB_ORACLE_PWD)

    # ssh_db_root.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh_db_root.connect(app_params.DB_IP, port=22, username='root', password=app_params.DB_ROOT_PWD)

    # 1. Prerequisite

    # 2. Prompt the User variables

    # 3. Clear the logs
    if tool_selection.CLEAR_LOGS:
        print('Clearing Logs')
        all_loggers.logger_log.info(f'''Clearing the Logs at
            rm -rf {app_params.SYSTEMI_PATH}/Apache/logs/*
            rm -rf {app_params.SYSTEMI_PATH}/Tomcat/logs/*.*
            rm -rf {app_params.SYSTEMI_PATH}/Systemi/log/*.*''')

        ssh_command(ssh_app, f'rm -rf {app_params.SYSTEMI_PATH}/Apache/logs/*')
        ssh_command(ssh_app, f'rm -rf {app_params.SYSTEMI_PATH}/Tomcat/logs/*.*')
        ssh_command(ssh_app, f'rm -rf {app_params.SYSTEMI_PATH}/Systemi/log/*.*')

    if tool_selection.CLEAR_THREAD_DUMP:
        print('Clearing Thread Dump')
        all_loggers.logger_log.info(f'''Clearing Thread Dump at rm -rf {app_params.THREAD_DUMP_LOCATION}/*.*')''')
        ssh_command(ssh_app, f'rm -rf {app_params.THREAD_DUMP_LOCATION}/*.*')

    # 4. Stopping the App Services
    if tool_selection.STOP_APP_SERVICES:
        all_loggers.logger_log.info('Stopping App Services')
        print('Stopping App Services')
        ssh_command(ssh_app, f'{app_params.SYSTEMI_PATH}/Systemi/bin/S99systemi.sh stop')

    # 5. Config tool
    if tool_selection.CONFIG_TOOL:
        print('Running Config Tool')
        all_loggers.logger_log.info('Running Config Tool')
        config_tool_status = config_tool_workflow.run_config_tool(app_params)
        all_loggers.logger_log.info(f'config_tool_status: {config_tool_status}')
        print(f'config_tool_status: {config_tool_status}')
        if not config_tool_status:
            print('Config tool Has returned the fail Status')
            raise Exception('Config tool Has returned the fail Status')

    if tool_selection.JAVA_JIT_ENABLED_SET_FALSE:
        print('Setting JAVA_JIT_ENABLED to False ')
        all_loggers.logger_log.info('Setting JAVA_JIT_ENABLED to False ')

        ssh_db_ora.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_db_ora.connect(app_params.DB_IP, port=22, username='oracle', password=app_params.DB_ORACLE_PWD)
        cmd_for_java_jit = '''
                sqlplus / as 'sysdba' <<!
                alter system set JAVA_JIT_ENABLED= FALSE;
                !'''
        ssh_command(ssh_db_ora, cmd_for_java_jit)

    # 6. If DB services UP, start App services

    if tool_selection.START_APP_SERVICES:
        print('starting app services')
        all_loggers.logger_log.info('starting app services')
        ts_start, wait_time = dt.now(), 120
        while True:
            all_loggers.logger_log.info(f'''
            started to wait at: {ts_start} 
            Now: {dt.now()}
            time passed: {(dt.now() - ts_start).total_seconds()}Secs of {wait_time} secs
            ''')
            time.sleep(1)
            try:
                dsn_tns = cx_Oracle.makedsn(app_params.DB_IP,
                                            app_params.ORACLE_DB_PORT,
                                            service_name=app_params.ORACLE_DB_ID)
                with cx_Oracle.connect(user=app_params.SCHEMA_NAME, password=app_params.SCHEMA_PWD, dsn=dsn_tns) as con:
                    break
            except Exception as e:
                all_loggers.logger_log.info(f'''Waiting for DB Connectivity: {e}
                {app_params.SCHEMA_NAME}/{
                app_params.SCHEMA_PWD}@{
                app_params.DB_IP}:{
                app_params.ORACLE_DB_PORT}/{
                app_params.ORACLE_DB_ID}''')
            if (dt.now() - ts_start).total_seconds() > wait_time:
                raise Exception(f'Wait time for Oracle DB({wait_time} sec) has expired.')
        all_loggers.logger_log.info('DB Connectible, Starting Services')
        ssh_command(ssh_app, f'{app_params.SYSTEMI_PATH}/Systemi/bin/S99systemi.sh start')

    # 7. If Monitors are working

    # 8. read the No of users in the scenario
    # 8.1 Load the NL Project

    if tool_selection.LOAD_NEOLOAD_PROJECT:
        print('Loading NL Project')
        all_loggers.logger_log.info('Checking If File System Available for Remote Machine')
        if not os.path.exists(app_params.EXECUTION_PROJECT_FOLDER):
            all_loggers.logger_log.info('Not Found, File System for Remote Machine, Mounting')
            remote_drive_mounter.mount(app_params.EXECUTION_PROJECT_FOLDER,
                                       app_params.WINDOWS_USER_NAME,
                                       app_params.WINDOWS_USER_PWD)
        all_loggers.logger_log.info('File System for Remote Machine, Connected')
        CONFIG_FILE_PATH = glob(os.path.join(app_params.EXECUTION_PROJECT_FOLDER, 'config.zip'))[0]
        NLP_FILE_NAME = glob(os.path.join(app_params.EXECUTION_PROJECT_FOLDER, '*.nlp'))[0]

        print(f'CONFIG_FILE_PATH: {CONFIG_FILE_PATH}')
        print(f'NLP_FILE_NAME: {NLP_FILE_NAME}')
        all_loggers.logger_log.info(f'CONFIG_FILE_PATH: {CONFIG_FILE_PATH} and NLP_FILE_NAME: {NLP_FILE_NAME}')

        _ = app_params.EXECUTION_PROJECT_FOLDER.split('$')
        RELATIVE_PROJECT_LOCATION = f'{_[0][-1]}:{_[1]}'

        print(f'RELATIVE_PROJECT_LOCATION: {RELATIVE_PROJECT_LOCATION}')
        all_loggers.logger_log.info(f'RELATIVE_PROJECT_LOCATION: {RELATIVE_PROJECT_LOCATION}')

        RELATIVE_NLP_FILE_NAME = os.path.join(RELATIVE_PROJECT_LOCATION, os.path.basename(
            glob(os.path.join(app_params.EXECUTION_PROJECT_FOLDER, '*.nlp'))[0]))

        print(f'RELATIVE_NLP_FILE_NAME: {RELATIVE_NLP_FILE_NAME}')
        all_loggers.logger_log.info(f'RELATIVE_NLP_FILE_NAME: {RELATIVE_NLP_FILE_NAME}')

        with zipfile.ZipFile(CONFIG_FILE_PATH) as archive:
            repo_file = archive.read("scenario.xml")
            archive.close()
        all_loggers.logger_log.info('Zip file reading completed.')

        tree = Et.ElementTree(Et.fromstring(repo_file))
        root = tree.getroot()
        scenario = root.find(f'scenario[@uid="{app_params.EXECUTION_SCENARIO}"]')
        volume_policy_entries = scenario.findall('population-policy/volume-policy-entry')
        total_users_in_scenario_list = []
        for volume_policy_entry in volume_policy_entries:
            policy = volume_policy_entry.find('rampup-volume-policy')
            if policy is not None:
                total_users_in_scenario_list.append(int(policy.attrib['maxUserNumber']))
                continue
            policy = volume_policy_entry.find('constant-volume-policy')
            if policy is not None:
                total_users_in_scenario_list.append(int(policy.attrib['userNumber']))
                continue

        total_users_in_scenario = sum(total_users_in_scenario_list)

        nl_status = ''
        try:
            resp_project_status = requests.post(url_project_status_d, data=json.dumps({"d": {}}), headers=headers)
            if resp_project_status.status_code != 201:
                nl_status = resp_project_status.text
            else:
                nl_status = resp_project_status.json()['d']['Status']

        except requests.exceptions.ConnectionError:
            nl_status = 'NL-NOT-ACCESSIBLE'
        all_loggers.logger_log.info(f'nl_status: {nl_status}')

        if nl_status in ['NL-NOT-ACCESSIBLE', ]:
            rce = Client(app_params.EXECUTION_IP,
                         username=app_params.WINDOWS_USER_NAME,
                         password=app_params.WINDOWS_USER_PWD)
            rce.connect()
            all_loggers.logger_log.info('RCE connected, Service creation in Progress')
            rce.create_service()
            all_loggers.logger_log.info('RCE service created...')
            session_output = rce.run_executable("cmd.exe",
                                                arguments='/c query session administrator')[0].decode().splitlines()
            cont_row = [i.strip() for i in session_output if i.strip() != ""][1]
            all_loggers.logger_log.info(f'cont_row: {cont_row}')
            # splitlines =  ['SESSION_NAME USERNAME ID  STATE   TYPE   DEVICE', 'rdp-tcp#3 Administrator  2  Active']
            rdp_session_id = [i.strip() for i in cont_row.split(' ') if i.strip() != ""][2]
            print(f'rdp_session_id: {rdp_session_id}')
            all_loggers.logger_log.info(f'rdp_session_id: {rdp_session_id}')

            command_to_run_nl = [
                r"C:\Users\rajveer.singh\Downloads\PSTools\PsExec.exe",
                r'-s',  # '-d',
                '-i', f'{rdp_session_id}',
                fr'\\{app_params.EXECUTION_IP}',
                '-u', f'{app_params.WINDOWS_USER_NAME}',
                '-p', f'{app_params.WINDOWS_USER_PWD}',
                fr'{app_params.NL_BIN_DIR}\NeoLoadGUI.exe',
                '-leaseLicense',
                f'{app_params.NL_LICENSE_ID}:{total_users_in_scenario}:{app_params.NL_LICENSE_LEASE_H}',
                '-project', fr'{RELATIVE_NLP_FILE_NAME}',
                '-NTS', app_params.NTS,
                '-NTSLogin', app_params.NTS_LOGIN,
            ]
            print(command_to_run_nl, 'command_to_run_nl')
            all_loggers.logger_log.info(f'command_to_run_nl: {command_to_run_nl}')
            alp = subprocess.Popen(command_to_run_nl)

        elif nl_status in ['NO_PROJECT', ]:
            resp = requests.post(url_project_open,
                                 json.dumps({"d": {"FilePath": RELATIVE_NLP_FILE_NAME}}),
                                 headers=headers)
        elif nl_status in ['READY', ]:
            resp = requests.post(url_is_project_open,
                                 json.dumps({"d": {"FilePath": RELATIVE_NLP_FILE_NAME}}),
                                 headers=headers)
            if not resp.json()['d']['Open']:
                print(f'Some Other Project is Opened. Not {RELATIVE_NLP_FILE_NAME}')
                raise Exception(f'Some Other Project is Opened. Not {RELATIVE_NLP_FILE_NAME}')
        else:
            # NL - RECORDING - NOT - LICENSED
            print(nl_status, 'exiting the tool')
            raise Exception(f'Unknown NL Status Encountered: {nl_status}')

    # 9 start the Test
    if tool_selection.START_TEST:
        all_loggers.logger_log.info('Stating the Test')
        print('Stating the Test')
        ts_start, wait_time = dt.now(), 180

        while True:
            all_loggers.logger_log.info(f'''
            started to wait at: {ts_start} 
            Now: {dt.now()}
            time passed: {(dt.now() - ts_start).total_seconds()}Secs of {wait_time} secs
            ''')
            time.sleep(1)
            try:
                resp_project_status = requests.post(url_project_status_d, data=json.dumps({"d": {}}), headers=headers)
                if resp_project_status.status_code == 201:
                    nl_status = resp_project_status.json()['d']['Status']
                    if nl_status == 'READY':
                        break
                    else:
                        all_loggers.logger_log.info(nl_status)
                else:
                    all_loggers.logger_log.info(resp_project_status.text)
            except Exception as e:
                all_loggers.logger_log.info(e)

            if (dt.now() - ts_start).total_seconds() > wait_time:
                raise Exception(f'Wait time for Project to Load ({wait_time} sec) has expired.')

        fts = dt.now().strftime('%b %d, %Y At %I-%M-%S %p')
        run_name = f'{app_params.APP} - {app_params.TEST_TYPE} {app_params.TEST_RUN_NO} - {fts}'
        run_desc = f'''{run_name} 
{app_params.TEST_DESCRIPTION}
Changes Made: 
    {f'{nl}{_____}'.join(json.loads(app_params.CHANGES_MADE))}

Test Scope:
    {f'{nl}{_____}'.join(json.loads(app_params.TEST_SCOPE))}

Meta: 
    {app_params.APP}
    {_____}{app_params.APP_IP}{_____}{app_params.DB_IP}{_____}{app_params.EXECUTION_IP} 
    {_____}{app_params.SYSTEMI_PATH} 
    {_____}{app_params.DB_HOME} 
    {_____}{app_params.SCHEMA_NAME}{_____}{app_params.ORACLE_DB_PORT}{_____}{app_params.ORACLE_DB_ID}
        '''

        data = {"d": {
            "ScenarioName": app_params.EXECUTION_SCENARIO,
            "TestResultName": run_name,
            "Description": run_desc
        }}

        print(json.dumps(data))

        resp = requests.post(url_start_test, data=json.dumps(data), headers=headers)
        print(resp.status_code)

        if resp.status_code == 201:
            print(json.dumps(resp.json(), indent=2))
        else:
            print(resp.text)

    # 10 thread dump
    if tool_selection.TAKE_THREADDUMP:
        _, output, _ = ssh_command(ssh_conn=ssh_app, cmd='netstat -nap | grep 8888')

        pid_row = [i.strip() for i in output.readlines() if i.split('jmxremote.port')[1][0].strip() == '='][0]
        jvm_pid = [i.strip() for i in pid_row.split(' ') if i.strip() != ''][1]

        cmd_thread_dump = f'nohup bash "{app_params.THREADDUMP_FILE_PATH}" {jvm_pid} </dev/null >/dev/null 2>&1 &'''
        ssh_command(ssh_conn=ssh_app, cmd=cmd_thread_dump)

    if tool_selection.TRUNCATE_DB_LOGS:
        all_loggers.logger_log.info(f'''''Truncating DB Logs @ {app_params.DB_IP}, {
        app_params.ORACLE_DB_PORT}, {app_params.ORACLE_DB_ID}''')
        print('Truncating DB Logs')
        dsn_tns = cx_Oracle.makedsn(app_params.DB_IP,
                                    app_params.ORACLE_DB_PORT,
                                    service_name=app_params.ORACLE_DB_ID)
        with cx_Oracle.connect(user=app_params.SCHEMA_NAME, password=app_params.SCHEMA_PWD, dsn=dsn_tns) as con:
            with con.cursor() as curs:
                curs.execute('Truncate table SI_INFOLET_RUN_PARAMETERS_LOG')
                curs.execute('Truncate table si_infolet_run_statistics')
                curs.execute('Truncate table ms_apps_mdf_errors')
                curs.execute('Truncate table ms_apps_message_log')
                curs.execute('Truncate table si_db_log')
                curs.execute('Truncate table si_sp_email_info')
                curs.execute('Truncate table ms_grc_flow_log')
                curs.execute('truncate table SI_DB_LOG drop storage')
                curs.execute('truncate table si_infolet_run_statistics drop storage')
                curs.execute('truncate table si_infolet_run_parameters_log drop storage')
                curs.execute('truncate table si_email_queue_t drop storage')
                curs.execute('truncate table si_sp_email_info drop storage')

    if tool_selection.EXEC_DB_SNAPSHOT_PROCEDURE:
        ssh_db_ora.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_db_ora.connect(app_params.DB_IP, port=22, username='oracle', password=app_params.DB_ORACLE_PWD)
        cmd_for_db_snapshot = '''
        sqlplus / as 'sysdba' <<!
        exec dbms_workload_repository.create_snapshot;
        exec dbms_workload_repository.modify_snapshot_settings(interval => 15, retention => 50400);
        !'''
        ssh_command(ssh_db_ora, cmd_for_db_snapshot)

    if tool_selection.SYSTEMI_LOGS_VALUE_TO_ERROR:
        pass

    if tool_selection.DB_CACHE_RELATED_QUERY:

        pass

except Exception as e:
    all_loggers.logger_log.exception(e)
    print(e)
finally:
    if ssh_app:
        ssh_app.close()
    if ssh_db_ora:
        ssh_db_ora.close()
    # if ssh_db_root:
    #     ssh_db_root.close()
    try:
        rce.remove_service()
        rce.disconnect()
    except:
        pass
    print('Done')
