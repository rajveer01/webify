import json
import os
import sqlite3
import sys
import tempfile
import xml.etree.ElementTree as Et
import zipfile
from datetime import datetime as dt
from glob import glob
from math import ceil, floor

import requests
import win32net
import xlrd
from dotmap import DotMap
from svn.remote import RemoteClient as Rc
from unidecode import unidecode as ucd

import all_loggers
import cx_Oracle
import put_description

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


def format_nl_name(name):
    name = ' '.join(name.split())
    name = name if len(name) < 57 else name[0:12] + '...' + name[-40:]
    return name


try:
    with open(os.path.join(rel_run_logs_folder, json_file_name), 'r') as f:
        tool_selection = json.loads(f.read())

    # tool_selection = {
    #     'nl_desc': {'status': True, 'need_op': True, 'xml_handle': True},
    #     'reset_user_session': {'status': True, 'need_op': False, 'xml_handle': True, 'active': 'No',
    #                            'def': {'Yes': 'ON', 'No': 'OFF', 'Auto': 'AUTO'}},
    #     'override_think_time': {'status': False, 'need_op': False, 'xml_handle': True},
    #     'error_occurs': {'status': True, 'need_op': False, 'xml_handle': True, 'active': 'DO NOTHING',
    #                      'def': {'DO NOTHING': 'DO_NOTHING', 'GO TO NEXT ITERATION': 'GO_TO_NEXT_ITERATION',
    #                              'STOP AND START': 'STOP_AND_START'}},
    #     'assertion_fails': {'status': True, 'need_op': False, 'xml_handle': True, 'active': 'DO NOTHING',
    #                         'def': {'DO NOTHING': 'DO_NOTHING', 'GO TO NEXT ITERATION': 'GO_TO_NEXT_ITERATION',
    #                                 'STOP AND START': 'STOP_AND_START'}},
    #     'pacing': {'status': True, 'need_op': True, 'xml_handle': True, 'active': 'No Pacing',
    #                'def': {'No Pacing': 'MODE_NO_PACING', 'Pacing duration': 'MODE_PACING_SIMPLE',
    #                        'Pacing Duration Between': 'MODE_PACING_RANGE'}},
    #     'population': {'status': True, 'need_op': True, 'xml_handle': True},
    #     'delay': {'status': False, 'need_op': False, 'xml_handle': False},
    # }

    # Step 1. Read from SQL Lite
    helper_db_params = DotMap()
    nl = '\n'
    ____ = '\t'
    with sqlite3.connect(os.path.join(all_loggers.web_server_dir, 'helper.db')) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM HELPER_VARIABLES')
        for row in cursor.fetchall():
            setattr(helper_db_params, row[0], row[1])  # row: (oracle_db_cs, 'MS_PLAB/MS_PLAB@msstore:1522/db11203')

    all_loggers.logger_log.info(f'''helper db read and got values as {nl} {helper_db_params}''')

    svn_client = helper_db_params.svn_client
    oracle_client_Path = helper_db_params.oracle_client_Path
    oracle_db_cs = helper_db_params.oracle_db_cs

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
               FROM PLAB_SERVERS_T WHERE APP = :APP'''

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
               INSTALLERS_TO_AVOID
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
            installers_to_avoid = row_app_params[29].split(',') if row_app_params[29] else ''

            monitor_available = True if monitor_IP.upper() == 'NA' else False
            compare_with_old = True if bool(compare_with_old) else False
            wpm_matters = True if bool(wpm_matters) else False

    NEED_OP = any([v['need_op'] for _, v in tool_selection.items() if v['status']])
    XML_HANDLE = any([v['xml_handle'] for _, v in tool_selection.items() if v['status']])
    OP_SVN_LOCATION = svn_op_location
    SVN_USER_NAME = svn_user_name
    SVN_PASSWORD = svn_password
    HEADERS = {'Content-type': 'application/json'}

    IP = execution_IP
    temp = execution_project_folder.split('$')
    RELATIVE_PROJECT_LOCATION = f'{temp[0][-1]}:{temp[1]}'
    PROJECT_LOCATION = os.path.join(fr'\\{IP}', RELATIVE_PROJECT_LOCATION.replace(':', '$'))

    use_dict = dict()
    mount_folder = str(PROJECT_LOCATION).strip().replace('\\', '/')
    use_dict['remote'] = ucd(mount_folder)
    use_dict['password'] = ucd(windows_user_pwd)
    use_dict['username'] = ucd(windows_user_name)
    if not os.path.exists(PROJECT_LOCATION):
        print('mounting')
        try:
            win32net.NetUseAdd(None, 2, use_dict)
        except Exception as e:
            # all_loggers.logger_log.exception(e)
            raise e

    CONFIG_FILE_PATH = glob(os.path.join(PROJECT_LOCATION, 'config.zip'))[0]

    NLP_FILE_NAME = glob(os.path.join(PROJECT_LOCATION, '*.nlp'))[0]

    RELATIVE_NLP_FILE_NAME = os.path.join(
        RELATIVE_PROJECT_LOCATION,
        os.path.basename(glob(os.path.join(PROJECT_LOCATION, '*.nlp'))[0]))

    all_loggers.logger_log.info(f'''
Calculated the tool Parameters as: 
    {____}NEED_OP{____}=>{____}{NEED_OP}
    {____}XML_HANDLE{____}=>{____}{XML_HANDLE}
    {____}OP_SVN_LOCATION{____}=>{____}{OP_SVN_LOCATION}
    {____}SVN_USER_NAME{____}=>{____}{SVN_USER_NAME}
    {____}SVN_PASSWORD{____}=>{____}{SVN_PASSWORD}
    {____}IP{____}=>{____}{IP}
    {____}RELATIVE_PROJECT_LOCATION{____}=>{____}{RELATIVE_PROJECT_LOCATION}
    {____}PROJECT_LOCATION{____}=>{____}{PROJECT_LOCATION}
    {____}CONFIG_FILE_PATH{____}=>{____}{CONFIG_FILE_PATH}
    {____}NLP_FILE_NAME{____}=>{____}{NLP_FILE_NAME}
    {____}RELATIVE_NLP_FILE_NAME{____}=>{____}{RELATIVE_NLP_FILE_NAME}
''')

    url_get_children = f"http://{IP}:7400/Design/v1/Service.svc/GetChildren"
    url_get_element = f"http://{IP}:7400/Design/v1/Service.svc/GetElements"
    url_add_element = f"http://{IP}:7400/Design/v1/Service.svc/AddElement"
    url_is_project_open = f'http://{IP}:7400/Design/v1/Service.svc/IsProjectOpen'
    url_close_project = f'http://{IP}:7400/Design/v1/Service.svc/CloseProject'
    url_open_project = f'http://{IP}:7400/Design/v1/Service.svc/OpenProject'
    url_save_project = f'http://{IP}:7400/Design/v1/Service.svc/SaveProject'
    url_status = f'http://{IP}:7400/Runtime/v1/Service.svc/GetStatus'


    def add_delay(parent_uid):
        all_loggers.logger_log.info('Enter Into Delay Function')
        data_get_children = json.dumps({"d": {"Uid": parent_uid}})
        resp_get_children = requests.post(url_get_children, data=data_get_children, headers=HEADERS)
        if resp_get_children.status_code == 201:
            res_children = json.loads(resp_get_children.text)['d']['results']
            children_type_map = [
                {'Type': result['Element']['Type'], 'Uid': result['Element']['Uid']} for result in res_children
            ]
            for p in range(len(res_children) - 1, -1, -1):
                data_add_element = json.dumps(
                    {"d": {"Type": "Delay", "Index": f"{p}",
                           "Parent": parent_uid,
                           "JsonDefinition": '{"Name":"Delay_FP", "Duration":"${delay}"}'}
                     }
                )
                if children_type_map[p]['Type'] == 'Transaction' and (
                        p == 0 or children_type_map[p - 1]['Type'] != 'DELAY'):
                    resp_add_element = requests.post(url_add_element, data=data_add_element, headers=HEADERS)
                    if resp_add_element.status_code != 201:
                        raise Exception(f'Failed 2 add Delay {resp_add_element.status_code}{nl}{resp_add_element.text}')
                elif children_type_map[p]['Type'] == 'LOOP':
                    add_delay(children_type_map[p]['Uid'])
        else:
            raise Exception(f'Unable use the Children API {resp_get_children.status_code}{nl}{resp_get_children.text}')


    # save and Close the Project
    '''Check if NeoLoad is not Busy'''
    data_status = json.dumps({"d": {}})
    resp_status = requests.post(url_status, data=data_status, headers=HEADERS)
    if resp_status.status_code != 201:
        raise Exception(f'Unable to Use Status API {resp_status.status_code}{nl}{resp_status.text}')

    project_status = json.loads(resp_status.text)['d']['Status']
    if project_status != 'READY':
        raise Exception(f'NeoLoad Status is not Ready Project Status: {project_status}')

    '''Check If same Project is Open'''
    data_check = json.dumps({"d": {
        "FilePath": RELATIVE_NLP_FILE_NAME
    }})
    resp_check = requests.post(url_is_project_open, data=data_check, headers=HEADERS)
    if resp_check.status_code != 201:
        raise Exception(f'Cant Use "Check If same Project is Open" API {resp_check.status_code}{nl}{resp_check.text}')
    project_open = json.loads(resp_check.text)['d']['Open']
    if not project_open:
        raise Exception(f'Different Project is opened Than the passed in UI')

    '''close It'''
    data_close = json.dumps({"d": {
        "Save": True
    }})
    resp_close = requests.post(url_close_project, data=data_close, headers=HEADERS)
    if resp_close.status_code != 201:
        raise Exception(f'Unable to Use Close Project API {resp_close.status_code}{nl}{resp_close.text}')

    '''Reopen it'''
    # data_open = json.dumps({"d": {
    #     "FilePath": RELATIVE_NLP_FILE_NAME
    # }})
    # resp_open = requests.post(url_open_project, data=data_open, headers=HEADERS)

    all_loggers.logger_log.info('Reading the Repository File From Remote')
    print('Reading the Repository File From Remote')

    with zipfile.ZipFile(CONFIG_FILE_PATH) as archive:
        repo_xml_file = archive.read('repository.xml')
        repo_files = archive.namelist()
        if XML_HANDLE:
            archive.extractall(PROJECT_LOCATION)
    all_loggers.logger_log.info('Read Repository File From Remote')
    tree = Et.ElementTree(Et.fromstring(repo_xml_file))
    root = tree.getroot()

    user_paths = root.findall("virtual-user")
    user_path_names = [user_path.attrib['uid'] for user_path in user_paths]

    if XML_HANDLE:
        if NEED_OP:

            all_loggers.logger_log.info('Getting OP from SVN')
            print('Getting OP from SVN')

            client = Rc(url=OP_SVN_LOCATION, username=SVN_USER_NAME, password=SVN_PASSWORD)
            with tempfile.TemporaryDirectory() as tmp_dir:
                export_response = client.run_command('export', [OP_SVN_LOCATION, tmp_dir])
                excel_file = os.path.join(tmp_dir, os.path.basename(OP_SVN_LOCATION))

                all_loggers.logger_log.info('Got OP from SVN')
                print('Got OP from SVN')

                wb = xlrd.open_workbook(excel_file)
                sheet = wb.sheet_by_name('Perf Test Case Final')

                all_loggers.logger_log.info('Reading the Excel ANd Making Dict Out of it.')
                print('Reading the Excel ANd Making Dict Out of it.')

                sheet_dict = {}
                for i in range(1, sheet.nrows):
                    nl_txn_name = str(sheet.cell_value(i, 3)).strip()
                    key_nl = put_description.format_nl_name(nl_txn_name)
                    all_loggers.logger_log.info(f'{nl_txn_name} converted to {key_nl}')
                    if key_nl is None:
                        continue

                    json_dict = {
                        'op_txn_name': str(sheet.cell_value(i, 2)).encode().decode('ascii', 'ignore'),
                        'expected_response_time': float(sheet.cell_value(i, 4)).__round__(1),
                        'scenario': str(sheet.cell_value(i, 0)).encode().decode('ascii', 'ignore'),
                        'wpm': float(sheet.cell_value(i, 1)).__round__(2),
                        'pacing': float(sheet.cell_value(i, 6)).__round__(2),
                    }

                    sheet_dict[key_nl] = json_dict

                all_loggers.logger_log.info(f'Got Sheet Dict {json.dumps(sheet_dict, indent=____)}')
                print('Got Sheet Dict from XL')

            print(f"Doing Description: {tool_selection['nl_desc']['status']}")
            all_loggers.logger_log.info(f"Doing Description {tool_selection['nl_desc']['status']}")

            if tool_selection['nl_desc']['status']:
                put_description_resp = put_description.put_from_file(root, sheet_dict.copy())

            print(f"Doing Pacing: {tool_selection['pacing']['status']}")
            all_loggers.logger_log.info(f"Doing Pacing {tool_selection['pacing']['status']}")

            if tool_selection['pacing']['status']:
                pacing_sheet_dict = sheet_dict.copy()

                pacing_mode = tool_selection['pacing']['def'].get(tool_selection['pacing']['active'])
                print('pacing_mode', pacing_mode)

                print(f"Pacing Mode: {pacing_mode}")
                all_loggers.logger_log.info(f"Pacing Mode: {pacing_mode}")

                txns = [
                    txn for txn in root.findall('basic-logical-action-container')
                    if not (str(txn.attrib['name']).lower() in ['login', 'logout'] or str(txn.attrib['name'])[0] == '#')
                ]
                txn_name_list = []
                for txn in txns:
                    txn.attrib['pacingMode'] = pacing_mode
                    txn_name_list.append(format_nl_name(str(txn.attrib['name'])))

                if pacing_mode == 'MODE_NO_PACING':
                    pass
                else:
                    if pacing_mode == 'MODE_PACING_SIMPLE':
                        for txn in txns:
                            txn_name = format_nl_name(txn.attrib['name'])
                            pacing_value = pacing_sheet_dict[txn_name]['pacing']
                            txn.attrib['pacingValue'] = f'{pacing_value}'
                            txn_name_list.remove(txn_name), pacing_sheet_dict.pop(txn_name)

                            all_loggers.logger_log.info(f'Pacing for:{pacing_mode}{____}{txn_name},{____}{pacing_value}')

                    elif pacing_mode == 'MODE_PACING_RANGE':
                        for txn in txns:
                            txn_name = format_nl_name(txn.attrib['name'])
                            pacing_value = pacing_sheet_dict[txn_name]['pacing']
                            txn.attrib['pacingStart'] = f'{floor(int(pacing_value) * 0.5)}'
                            txn.attrib['pacingEnd'] = f'{ceil(int(pacing_value) * 1.5)}'

                            txn_name_list.remove(txn_name)
                            pacing_sheet_dict.pop(txn_name)

                            all_loggers.logger_log.info(f'Pacing for:{pacing_mode}{____}{txn_name},{____}{pacing_value}')

            # if tool_selection['population']['status']:
            #     pass

        print(f"Doing Reset User Session: {tool_selection['reset_user_session']['status']}")
        all_loggers.logger_log.info(f"Doing Reset User Session: {tool_selection['reset_user_session']['status']}")

        if tool_selection['reset_user_session']['status']:
            action_containers = root.findall('virtual-user/actions-container')
            reset_user_session_value = tool_selection.get(
                'reset_user_session').get('def').get(tool_selection.get('reset_user_session').get('active'))
            for action_container in action_containers:
                action_container.attrib.update({'clearUserIterationDataMode': reset_user_session_value})

        print(f"Doing Override Think time: {tool_selection['override_think_time']['status']}")
        all_loggers.logger_log.info(f"Doing Override Think time: {tool_selection['override_think_time']['status']}")

        if tool_selection['override_think_time']['status']:
            think_time_elements = root.findall('virtual-user/thinktime-policy')
            for think_time_element in think_time_elements:
                think_time_element.attrib.update({'thinktimePolicy': '1'})
                think_time_element.attrib.update({'thinktimeValue': '0'})

        print(f"Doing Error Occurs: {tool_selection['error_occurs']['status']}")
        all_loggers.logger_log.info(f"Doing Error Occurs: {tool_selection['error_occurs']['status']}")

        if tool_selection['error_occurs']['status']:
            scenarios = root.findall('virtual-user')
            error_occurs_value = tool_selection['error_occurs'].get('def').get(tool_selection['error_occurs']['active'])
            for scenario in scenarios:
                scenario.attrib.update({'errorPolicy': error_occurs_value})

        print(f"Doing Assertion Fails: {tool_selection['assertion_fails']['status']}")
        all_loggers.logger_log.info(f"Doing Assertion Fails: {tool_selection['assertion_fails']['status']}")

        if tool_selection['assertion_fails']['status']:
            scenarios = root.findall('virtual-user')
            assertion_fails_value = tool_selection.get('assertion_fails').get('def').get(
                tool_selection['assertion_fails']['active'])
            for scenario in scenarios:
                scenario.attrib.update({'failedAssertionPolicy': assertion_fails_value})

        all_loggers.logger_log.info('Writing to a File: Updated XML')
        print('Writing to a File: Updated XML')
        tree.write(os.path.join(PROJECT_LOCATION, 'repository.xml'))

        time_stamp = dt.now().strftime('%b %d, %Y At %I-%M-%S %p')
        os.rename(CONFIG_FILE_PATH, CONFIG_FILE_PATH.replace('config.zip', f'config {time_stamp}.zip'))

        with zipfile.ZipFile(CONFIG_FILE_PATH, 'w') as zipped:
            for file in repo_files:
                zipped.write(os.path.join(PROJECT_LOCATION, file), file)

        os.remove(os.path.join(PROJECT_LOCATION, 'repository.xml'))
        os.remove(os.path.join(PROJECT_LOCATION, 'scenario.xml'))
        os.remove(os.path.join(PROJECT_LOCATION, 'settings.xml'))

    '''Reopen it'''
    all_loggers.logger_log.info('Reopening the project')
    print('Reopening the project')
    data_open = json.dumps({"d": {
        "FilePath": RELATIVE_NLP_FILE_NAME
    }})
    resp_open = requests.post(url_open_project, data=data_open, headers=HEADERS)

    print(f"Doing Delay: {tool_selection['delay']['status']}")
    all_loggers.logger_log.info(f"Doing Delay: {tool_selection['delay']['status']}")
    if tool_selection['delay']['status']:
        for user_path_name in user_path_names:
            all_loggers.logger_log.info(f'Doing Delay For: {user_path_name}')
            add_delay(f"$parent={user_path_name};$index=1")

    # save project
    data_save = json.dumps({"d": {}})
    resp_open = requests.post(url_save_project, data=data_save, headers=HEADERS)

    print('Done')

except Exception as e:
    print(e)
    all_loggers.logger_log.info([print(f'{_} ==> {v}') for _, v in globals().copy().items() if '__' not in _])
    all_loggers.logger_log.exception(e)
    raise e
