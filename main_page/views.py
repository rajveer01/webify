from django.shortcuts import render, redirect
from django.http import HttpResponse
import cx_Oracle
from dotmap import DotMap
import sqlite3
import json
import os
import subprocess
from datetime import datetime as dt

local_db_vars = DotMap()

with sqlite3.connect('helper.db') as local_db_conn:
    cursor_sql = local_db_conn.cursor()
    cursor_sql.execute('SELECT * From helper_variables')
    for row in cursor_sql.fetchall():
        setattr(local_db_vars, row[0], row[1])
local_db_conn.close()


def home(request):
    return render(request, 'main_page/index.html')


def app_parameters(request):
    app_name = request.POST.get('app_name')
    if not app_name:
        return HttpResponse('<h1> Empty App Name. </h1>')

    run_tool = request.POST.get('run_tool')
    if run_tool == 'sla_sheet_generator':
        return render(request, 'sla_sheet_generator/download_page.html', context={'app_name': app_name})

    with cx_Oracle.connect(local_db_vars.oracle_db_cs) as conn:
        with conn.cursor() as curs:
            sql_app_name = 'SELECT * FROM  PLAB_SERVERS_T where APP = :app'
            curs.execute(sql_app_name, {'app': app_name})
            curs.rowfactory = lambda *args: dict(zip([d[0] for d in curs.description], args))
            server_dict = curs.fetchone()

            sql_app_name = 'SELECT * FROM  PLAB_APP_PARAMETERS where APP = :app'
            curs.execute(sql_app_name, {'app': app_name})
            curs.rowfactory = lambda *args: dict(zip([d[0] for d in curs.description], args))
            param_dict = curs.fetchone()

            server_dict = dict() if server_dict is None else server_dict
            param_dict = dict() if param_dict is None else param_dict

            server_dict.update(param_dict)
            server_dict['TEST_SCOPE'] = server_dict.get('TEST_SCOPE', '')
            server_dict['CHANGES_MADE'] = server_dict.get('CHANGES_MADE', '')
            server_dict['TO_MAIL_FILE'] = server_dict.get('TO_MAIL_FILE', '')

            server_dict['TEST_SCOPE'] = '\n'.join(json.loads(server_dict['TEST_SCOPE'].read())) if server_dict[
                'TEST_SCOPE'] else ''
            server_dict['CHANGES_MADE'] = '\n'.join(json.loads(server_dict['CHANGES_MADE'].read())) if server_dict[
                'CHANGES_MADE'] else ''
            server_dict['TO_MAIL_FILE'] = '\n'.join(json.loads(server_dict['TO_MAIL_FILE'].read())) if server_dict[
                'TO_MAIL_FILE'] else ''

            server_dict['ADDITIONAL_FILES_APP'] = '\n'.join(
                json.loads(server_dict['ADDITIONAL_FILES_APP'].read())
            ) if server_dict['ADDITIONAL_FILES_APP'] else ''

            server_dict['ADDITIONAL_FILES_DB'] = '\n'.join(
                json.loads(server_dict['ADDITIONAL_FILES_DB'].read())
            ) if server_dict['ADDITIONAL_FILES_DB'] else ''

            server_dict['ADDITIONAL_DIRS_APP'] = '\n'.join(
                json.loads(server_dict['ADDITIONAL_DIRS_APP'].read())
            ) if server_dict['ADDITIONAL_DIRS_APP'] else ''

            server_dict['ADDITIONAL_DIRS_DB'] = '\n'.join(
                json.loads(server_dict['ADDITIONAL_DIRS_DB'].read())
            ) if server_dict['ADDITIONAL_DIRS_DB'] else ''

            x = local_db_vars.toDict()
            server_dict.update(x)

            server_dict['APP'] = app_name
            server_dict['EXECUTION_IP'] = server_dict.get('EXECUTION_IP', '')
            server_dict['EXECUTION_PROJECT_FOLDER'] = server_dict.get('EXECUTION_PROJECT_FOLDER', '')
            server_dict['EXECUTION_SCENARIO'] = server_dict.get('EXECUTION_SCENARIO', '')
            server_dict['MONITOR_IP'] = server_dict.get('MONITOR_IP', '')
            server_dict['MONITOR_PROJECT_LOCATION'] = server_dict.get('MONITOR_PROJECT_LOCATION', '')
            server_dict['MONITOR_SCENARIO'] = server_dict.get('MONITOR_SCENARIO', '')
            server_dict['TEST_RUN_NO'] = server_dict.get('TEST_RUN_NO', '')
            server_dict['TEST_DESCRIPTION'] = server_dict.get('TEST_DESCRIPTION', '')
            server_dict['RELEASE_NAME'] = server_dict.get('RELEASE_NAME', '')
            server_dict['ARTIFACTS_FOLDER'] = server_dict.get('ARTIFACTS_FOLDER', '')
            server_dict['SVN_ARTIFACT_FOLDER'] = server_dict.get('SVN_ARTIFACT_FOLDER', '')
            server_dict['SVN_OP_LOCATION'] = server_dict.get('SVN_OP_LOCATION', '')
            server_dict['SVN_USER_NAME'] = server_dict.get('SVN_USER_NAME', '')
            server_dict['SVN_PASSWORD'] = server_dict.get('SVN_PASSWORD', '')
            server_dict['TOTAL_USERS'] = server_dict.get('TOTAL_USERS', '')
            server_dict['CHANGE_HISTORY'] = server_dict.get('CHANGE_HISTORY', '')
            server_dict['ORACLE_DB_PORT'] = server_dict.get('ORACLE_DB_PORT', '')
            server_dict['ORACLE_DB_ID'] = server_dict.get('ORACLE_DB_ID', '')
            server_dict['COMPARE_WITH_OLD'] = server_dict.get('COMPARE_WITH_OLD', '')
            server_dict['WPM_MATTERS'] = server_dict.get('WPM_MATTERS', '')
            server_dict['TEST_TYPE'] = server_dict.get('TEST_TYPE', '')
            server_dict['THREAD_DUMP_LOCATION'] = server_dict.get('THREAD_DUMP_LOCATION', '')
            server_dict['HEAP_DUMP_LOCATION'] = server_dict.get('HEAP_DUMP_LOCATION', '')
            server_dict['OLD_RUN'] = server_dict.get('OLD_RUN', '')
            server_dict['OLD_TEST_TYPE'] = server_dict.get('OLD_TEST_TYPE', '')
            server_dict['OLD_RELEASE_NAME'] = server_dict.get('OLD_RELEASE_NAME', '')
            server_dict['TEST_SCOPE'] = server_dict.get('TEST_SCOPE', '')
            server_dict['CHANGES_MADE'] = server_dict.get('CHANGES_MADE', '')
            server_dict['TO_MAIL_FILE'] = server_dict.get('TO_MAIL_FILE', '')
            server_dict['INSTALLERS_TO_AVOID'] = server_dict.get('INSTALLERS_TO_AVOID', '')
            server_dict['APP_IP'] = server_dict.get('APP_IP', '')
            server_dict['DB_IP'] = server_dict.get('DB_IP', '')
            server_dict['SYSTEMI_PATH'] = server_dict.get('SYSTEMI_PATH', '')
            server_dict['DB_HOME'] = server_dict.get('DB_HOME', '')
            server_dict['SCHEMA_NAME'] = server_dict.get('SCHEMA_NAME', '')
            server_dict['SCHEMA_PWD'] = server_dict.get('SCHEMA_PWD', '')
            server_dict['APP_ORACLE_PWD'] = server_dict.get('APP_ORACLE_PWD', '')
            server_dict['APP_ROOT_PWD'] = server_dict.get('APP_ROOT_PWD', '')
            server_dict['DB_ORACLE_PWD'] = server_dict.get('DB_ORACLE_PWD', '')
            server_dict['DB_ROOT_PWD'] = server_dict.get('DB_ROOT_PWD', '')
            server_dict['THREADDUMP_FILE_PATH'] = server_dict.get('THREADDUMP_FILE_PATH', '')
            server_dict['WINDOWS_IP'] = server_dict.get('WINDOWS_IP', '')
            server_dict['ACTIVATION_FOR_THIS_RELEASE'] = server_dict.get('ACTIVATION_FOR_THIS_RELEASE', '')
            server_dict['JDK_PATH'] = server_dict.get('JDK_PATH', '')
            server_dict['svn_client'] = server_dict.get('svn_client', '')
            server_dict['oracle_client_Path'] = server_dict.get('oracle_client_Path', '')
            server_dict['oracle_db_cs'] = server_dict.get('oracle_db_cs', '')

            server_dict['all_monitors'] = json.loads(server_dict.get('all_monitors', ''))
            server_dict['test_types'] = json.loads(server_dict.get('test_types', ''))
            server_dict['old_test_types'] = server_dict['test_types'].copy()

            if server_dict['MONITOR_IP'] in server_dict['all_monitors']:
                server_dict['all_monitors'].remove(server_dict['MONITOR_IP'])
                server_dict['all_monitors'].insert(0, server_dict['MONITOR_IP'])

            if server_dict['TEST_TYPE'] in server_dict['test_types']:
                server_dict['test_types'].remove(server_dict['TEST_TYPE'])
                server_dict['test_types'].insert(0, server_dict['TEST_TYPE'])

            if server_dict['OLD_TEST_TYPE'] in server_dict['test_types']:
                server_dict['test_types'].remove(server_dict['OLD_TEST_TYPE'])
                server_dict['test_types'].insert(0, server_dict['OLD_TEST_TYPE'])

            sql_release_name = '''SELECT RELEASE_NAME FROM (SELECT RELEASE_NAME FROM PT_RESULTS GROUP BY 
                                    RELEASE_NAME ORDER BY MAX(ROW_ID) DESC) WHERE ROWNUM < 6'''

            curs.execute(sql_release_name)
            release_list = [li[0] for li in curs.fetchall()]
            if server_dict['RELEASE_NAME'] in release_list:
                release_list.remove(server_dict['RELEASE_NAME'])
            release_list.insert(0, server_dict['RELEASE_NAME'])

            server_dict['release_list'] = release_list

            old_release_list = release_list.copy()
            old_release_list.insert(0, 'NA')
            if server_dict['OLD_RELEASE_NAME'] in old_release_list:
                old_release_list.remove(server_dict['OLD_RELEASE_NAME'])
            old_release_list.insert(0, server_dict['OLD_RELEASE_NAME'])

            server_dict['old_release_list'] = old_release_list

            query_run = '''
                            SELECT COALESCE(MAX(Test_Run_No), 0) FROM PT_RESULTS WHERE 
                            RELEASE_NAME = :Release_Name and APP_NAME = :App_Name and TEST_TYPE = :Test_type
                            '''
            query_run_format = {'Release_Name': server_dict['RELEASE_NAME'], 'App_Name': server_dict['APP'],
                                'Test_type': server_dict['TEST_TYPE']}
            curs.execute(query_run, query_run_format)
            run_no = curs.fetchone()[0]
            run_no = int(run_no) + 1
            server_dict['TEST_RUN_NO'] = run_no.__str__()

            query_old_run = '''
            SELECT COALESCE(MAX(Test_Run_No), 0) As Run_Number FROM PT_RESULTS WHERE RELEASE_NAME = :Release_Name 
            and APP_NAME = :App_Name and TEST_TYPE = :old_test_type
            '''
            query_run_format = {'Release_Name': server_dict['OLD_RELEASE_NAME'], 'App_Name': server_dict['APP'],
                                'old_test_type': server_dict['OLD_TEST_TYPE']}
            curs.execute(query_old_run, query_run_format)
            old_run_no = curs.fetchone()[0]
            old_run_no = int(old_run_no)
            server_dict['OLD_RUN'] = old_run_no.__str__()

            server_dict['run_tool'] = run_tool
    if run_tool == 'sla_sheet_generator':
        return render(request, 'sla_sheet_generator/download_page.html', context=server_dict)
    return render(request, 'main_page/app_parameters.html', context=server_dict)


def app_parameters_submit(request):
    if request.method != "POST":
        return render(request, 'main_page/run_tracker.html')

    app_name = request.POST.get('app_name')
    run_tool = request.POST.get('run_tool')
    execution_ip = request.POST.get('execution_ip')
    exec_project_folder = request.POST.get('exec_project_folder')
    exec_scenario = request.POST.get('exec_scenario')
    monitor_ip = request.POST.get('monitor_ip') if request.POST.get('monitor_ip') else "NA"
    # monitor_ip = monitor_ip if monitor_ip else "NA"
    monitor_project_folder = request.POST.get('monitor_project_folder')
    moni_test_scenarios = request.POST.get('moni_test_scenarios')
    run = request.POST.get('run')
    run_description = request.POST.get('run_description')
    release_list_name = request.POST.get('release_list')
    test_type = request.POST.get('test_type')
    app_ip = request.POST.get('app_ip')
    db_ip = request.POST.get('db_ip')
    SystemI_Path = request.POST.get('SystemI_Path')
    db_home = request.POST.get('db_home')
    schema_name = request.POST.get('schema_name')
    schema_pwd = request.POST.get('schema_pwd')
    App_Oracle_PWD = request.POST.get('App_Oracle_PWD')
    App_Root_PWD = request.POST.get('App_Root_PWD')
    DB_Oracle_PWD = request.POST.get('DB_Oracle_PWD')
    DB_Root_PWD = request.POST.get('DB_Root_PWD')
    svn_artifact_folder = request.POST.get('svn_artifact_folder')
    svn_op_location = request.POST.get('svn_op_location')
    svn_user_name = request.POST.get('svn_user_name')
    svn_password = request.POST.get('svn_password')
    total_users = request.POST.get('total_users')
    change_history = request.POST.get('change_history')
    changes_made = json.dumps(request.POST.get('changes_made').split('\n'))
    tes_scope = json.dumps(request.POST.get('tes_scope').split('\n'))
    to_mail_file = json.dumps(request.POST.get('to_mail_file').split('\n'))
    old_release_list_name = request.POST.get('old_release_list')
    old_test_type = request.POST.get('old_test_type')
    old_run = request.POST.get('old_run')
    oracle_db_port = request.POST.get('oracle_db_port')
    oracle_db_id = request.POST.get('oracle_db_id')
    compare_with_old = request.POST.get('compare_with_old', 0)
    thread_dump_location = request.POST.get('thread_dump_location')
    heap_dump_location = request.POST.get('heap_dump_location')
    installers_to_avoid = request.POST.get('installers_to_avoid')
    jdk_path = request.POST.get('jdk_path')

    additional_files_app = [_.strip() for _ in str(request.POST.get('additional_files_app')).splitlines()]
    additional_files_db = [_.strip() for _ in str(request.POST.get('additional_files_db')).splitlines()]
    additional_dirs_app = [_.strip() for _ in str(request.POST.get('additional_dirs_app')).splitlines()]
    additional_dirs_db = [_.strip() for _ in str(request.POST.get('additional_dirs_db')).splitlines()]

    new_sql = '''
    BEGIN
        BEGIN	
            INSERT INTO PLAB_SERVERS_T(APP,
            APP_IP, DB_IP, SYSTEMI_PATH, DB_HOME, SCHEMA_NAME, SCHEMA_PWD, APP_ORACLE_PWD,
            APP_ROOT_PWD, DB_ORACLE_PWD, DB_ROOT_PWD, THREADDUMP_FILE_PATH, WINDOWS_IP,
            ACTIVATION_FOR_THIS_RELEASE, JDK_PATH)
            VALUES
            (:APP, :APP_IP, :DB_IP, :SYSTEMI_PATH, :DB_HOME, :SCHEMA_NAME, :SCHEMA_PWD, 
            :APP_ORACLE_PWD, :APP_ROOT_PWD, :DB_ORACLE_PWD, :DB_ROOT_PWD, :THREADDUMP_FILE_PATH,
            :WINDOWS_IP, :ACTIVATION_FOR_THIS_RELEASE, :JDK_PATH);
            EXCEPTION
            WHEN DUP_VAL_ON_INDEX  THEN
                UPDATE PLAB_SERVERS_T SET 
                APP_IP = :APP_IP,
                DB_IP = :DB_IP,
                SYSTEMI_PATH = :SYSTEMI_PATH,
                DB_HOME = :DB_HOME,
                SCHEMA_NAME = :SCHEMA_NAME,
                SCHEMA_PWD = :SCHEMA_PWD,
                APP_ORACLE_PWD = :APP_ORACLE_PWD,
                APP_ROOT_PWD = :APP_ROOT_PWD,
                DB_ORACLE_PWD = :DB_ORACLE_PWD,
                DB_ROOT_PWD = :DB_ROOT_PWD,
                THREADDUMP_FILE_PATH = :THREADDUMP_FILE_PATH,
                WINDOWS_IP = :WINDOWS_IP,
                ACTIVATION_FOR_THIS_RELEASE = :ACTIVATION_FOR_THIS_RELEASE,
                JDK_PATH = :JDK_PATH
                WHERE APP = :APP;
            END;
            BEGIN
                INSERT INTO PLAB_APP_PARAMETERS(
                APP, EXECUTION_IP, EXECUTION_PROJECT_FOLDER, EXECUTION_SCENARIO,
                MONITOR_IP, MONITOR_PROJECT_LOCATION, MONITOR_SCENARIO, TEST_RUN_NO,
                TEST_DESCRIPTION, RELEASE_NAME, ARTIFACTS_FOLDER, SVN_ARTIFACT_FOLDER,
                SVN_OP_LOCATION, SVN_USER_NAME, SVN_PASSWORD, TOTAL_USERS,
                CHANGE_HISTORY, ORACLE_DB_PORT, ORACLE_DB_ID, COMPARE_WITH_OLD,
                WPM_MATTERS, TEST_TYPE, THREAD_DUMP_LOCATION, HEAP_DUMP_LOCATION,
                OLD_RUN, OLD_TEST_TYPE, OLD_RELEASE_NAME, TEST_SCOPE, CHANGES_MADE,
                TO_MAIL_FILE, INSTALLERS_TO_AVOID, ADDITIONAL_FILES_APP, ADDITIONAL_FILES_DB, 
                ADDITIONAL_DIRS_APP, ADDITIONAL_DIRS_DB
                )
            
                VALUES
                (:APP, :EXECUTION_IP, :EXECUTION_PROJECT_FOLDER, :EXECUTION_SCENARIO,
                :MONITOR_IP, :MONITOR_PROJECT_LOCATION, :MONITOR_SCENARIO, :TEST_RUN_NO, 
                :TEST_DESCRIPTION, :RELEASE_NAME, :ARTIFACTS_FOLDER, :SVN_ARTIFACT_FOLDER, 
                :SVN_OP_LOCATION, :SVN_USER_NAME, :SVN_PASSWORD, :TOTAL_USERS, :CHANGE_HISTORY, 
                :ORACLE_DB_PORT, :ORACLE_DB_ID, :COMPARE_WITH_OLD, :WPM_MATTERS, :TEST_TYPE,
                :THREAD_DUMP_LOCATION, :HEAP_DUMP_LOCATION, :OLD_RUN, :OLD_TEST_TYPE, 
                :OLD_RELEASE_NAME, :TEST_SCOPE, :CHANGES_MADE, :TO_MAIL_FILE, 
                :INSTALLERS_TO_AVOID, :ADDITIONAL_FILES_APP, :ADDITIONAL_FILES_DB, 
                :ADDITIONAL_DIRS_APP, :ADDITIONAL_DIRS_DB);		
            EXCEPTION
            WHEN DUP_VAL_ON_INDEX  THEN
                UPDATE PLAB_APP_PARAMETERS SET
                EXECUTION_IP = :EXECUTION_IP,
                EXECUTION_PROJECT_FOLDER = :EXECUTION_PROJECT_FOLDER,
                EXECUTION_SCENARIO = :EXECUTION_SCENARIO,
                MONITOR_IP = :MONITOR_IP,
                MONITOR_PROJECT_LOCATION = :MONITOR_PROJECT_LOCATION,
                MONITOR_SCENARIO = :MONITOR_SCENARIO,
                TEST_RUN_NO = :TEST_RUN_NO,
                TEST_DESCRIPTION = :TEST_DESCRIPTION,
                RELEASE_NAME = :RELEASE_NAME,
                ARTIFACTS_FOLDER = :ARTIFACTS_FOLDER,
                SVN_ARTIFACT_FOLDER = :SVN_ARTIFACT_FOLDER,
                SVN_OP_LOCATION = :SVN_OP_LOCATION,
                SVN_USER_NAME = :SVN_USER_NAME,
                SVN_PASSWORD = :SVN_PASSWORD,
                TOTAL_USERS = :TOTAL_USERS,
                CHANGE_HISTORY = :CHANGE_HISTORY,
                ORACLE_DB_PORT = :ORACLE_DB_PORT,
                ORACLE_DB_ID = :ORACLE_DB_ID,
                COMPARE_WITH_OLD = :COMPARE_WITH_OLD,
                WPM_MATTERS = :WPM_MATTERS,
                TEST_TYPE = :TEST_TYPE,
                THREAD_DUMP_LOCATION = :THREAD_DUMP_LOCATION,
                HEAP_DUMP_LOCATION = :HEAP_DUMP_LOCATION,
                OLD_RUN = :OLD_RUN,
                OLD_TEST_TYPE = :OLD_TEST_TYPE,
                OLD_RELEASE_NAME = :OLD_RELEASE_NAME,
                TEST_SCOPE = :TEST_SCOPE,
                CHANGES_MADE = :CHANGES_MADE,
                TO_MAIL_FILE = :TO_MAIL_FILE,
                INSTALLERS_TO_AVOID = :INSTALLERS_TO_AVOID,
                ADDITIONAL_FILES_APP = :ADDITIONAL_FILES_APP, 
                ADDITIONAL_FILES_DB = :ADDITIONAL_FILES_DB, 
                ADDITIONAL_DIRS_APP = :ADDITIONAL_DIRS_APP, 
                ADDITIONAL_DIRS_DB = :ADDITIONAL_DIRS_DB
                WHERE APP = :APP;
            END; 
        END;
    '''

    log_time_stamp = dt.now().strftime('%b %d, %Y At %I-%M-%S %p')
    rel_run_log_folder, rel_artifact_folder = map(
        lambda k: os.path.join('Artifacts', release_list_name, app_name,
                               f'{app_name} - {release_list_name} - {test_type} {run} {log_time_stamp} - {k}'),
        ['Run Logs', 'Artifacts']
    )

    with cx_Oracle.connect(local_db_vars.oracle_db_cs) as plab_connection:
        with plab_connection.cursor() as curs:
            sql_format = {
                'APP': app_name,
                'EXECUTION_IP': execution_ip,
                'EXECUTION_PROJECT_FOLDER': exec_project_folder,
                'EXECUTION_SCENARIO': exec_scenario,
                'MONITOR_IP': monitor_ip,
                'MONITOR_PROJECT_LOCATION': monitor_project_folder,
                'MONITOR_SCENARIO': moni_test_scenarios,
                'TEST_RUN_NO': run,
                'TEST_DESCRIPTION': run_description,
                'RELEASE_NAME': release_list_name,
                'ARTIFACTS_FOLDER': rel_artifact_folder,
                'SVN_ARTIFACT_FOLDER': svn_artifact_folder,
                'SVN_OP_LOCATION': svn_op_location,
                'SVN_USER_NAME': svn_user_name,
                'SVN_PASSWORD': svn_password,
                'TOTAL_USERS': total_users,
                'CHANGE_HISTORY': change_history,
                'ORACLE_DB_PORT': oracle_db_port,
                'ORACLE_DB_ID': oracle_db_id,
                'COMPARE_WITH_OLD': compare_with_old,
                'WPM_MATTERS': 1 if test_type == 'Load Run' else 0,
                'TEST_TYPE': test_type,
                'THREAD_DUMP_LOCATION': thread_dump_location,
                'HEAP_DUMP_LOCATION': heap_dump_location,
                'OLD_RUN': old_run,
                'OLD_TEST_TYPE': old_test_type,
                'OLD_RELEASE_NAME': old_release_list_name,
                'TEST_SCOPE': tes_scope,
                'CHANGES_MADE': changes_made,
                'TO_MAIL_FILE': to_mail_file,
                'INSTALLERS_TO_AVOID': installers_to_avoid,
                'APP_IP': app_ip,
                'DB_IP': db_ip,
                'SYSTEMI_PATH': SystemI_Path,
                'DB_HOME': db_home,
                'SCHEMA_NAME': schema_name,
                'SCHEMA_PWD': schema_pwd,
                'APP_ORACLE_PWD': App_Oracle_PWD,
                'APP_ROOT_PWD': App_Root_PWD,
                'DB_ORACLE_PWD': DB_Oracle_PWD,
                'DB_ROOT_PWD': DB_Root_PWD,
                'THREADDUMP_FILE_PATH': '/data/oracle/tools/jstack_ThreadAutomate.sh',
                'WINDOWS_IP': execution_ip,
                'ACTIVATION_FOR_THIS_RELEASE': 'TRUE',
                'JDK_PATH': jdk_path,
                'ADDITIONAL_FILES_APP': json.dumps(additional_files_app),
                'ADDITIONAL_FILES_DB': json.dumps(additional_files_db),
                'ADDITIONAL_DIRS_APP': json.dumps(additional_dirs_app),
                'ADDITIONAL_DIRS_DB': json.dumps(additional_dirs_db),
            }

            curs.execute(new_sql, sql_format)
            plab_connection.commit()

    if run_tool == 'test_report_automation':

        std_log_file_name, std_out_file_name, std_err_file_name = map(
            lambda k: f'{app_name} - Run {run} - {log_time_stamp} - STD {k}.log',
            ['Log', 'Out', 'Err']
        )

        tool_dir = 'test_report_automation/the_tool'

        if not os.path.exists(f'{tool_dir}/{rel_run_log_folder}'):
            os.makedirs(f'{tool_dir}/{rel_run_log_folder}')
        if not os.path.exists(f'{tool_dir}/{rel_artifact_folder}'):
            os.makedirs(f'{tool_dir}/{rel_artifact_folder}')

        command_list = [
            'python',
            f'{tool_dir}/report_automation.py',  # file Name
            app_name,  # 1 App name ##IAD
            tool_dir,  # 2 tool directory to change CW directory ## test_report_automation/the_tool
            rel_run_log_folder,  # 3 Relative to tools directory for run logs After Changed directory
            # Artifacts\Feb Release 2020\REM\REM - Feb 2020 - Load Run 24 - Oct 12, 2020 at 10-12-39 PM - Run Logs
            rel_artifact_folder,  # 4 Relative to the tools directory for collecting artifacts
            # Artifacts\Feb Release 2020\REM\REM - Feb 2020 - Load Run 24 - Oct 12, 2020 at 10-12-39 PM - Artifacts
            std_log_file_name,  # 5 REM - Run 24 - Oct 12, 2020 at 10-12-39 PM - STD Log.log
            std_out_file_name,  # 6 REM - Run 24 - Oct 12, 2020 at 10-12-39 PM - STD Out.log
            std_err_file_name,  # 7 REM - Run 24 - Oct 12, 2020 at 10-12-39 PM - STD Err.log
        ]

        subprocess.Popen(command_list)
        context = {
            # Path of the File From Current Directory
            'run_log_file': f'{tool_dir}/{rel_run_log_folder}/{std_log_file_name}',
            'std_out_file': f'{tool_dir}/{rel_run_log_folder}/{std_out_file_name}',
            'std_err_file': f'{tool_dir}/{rel_run_log_folder}/{std_err_file_name}',
        }
        print('context', context)
        return render(request, 'main_page/run_tracker.html', context=context)

    if run_tool == 'nl_project_manager':
        nl_project_manager_selection = request.POST.get('nl_project_manager_selection')

        tool_dir = 'nl_project_manager/the_tool'

        std_log_file_name, std_out_file_name, std_err_file_name = map(
            lambda k: f'{app_name} - {log_time_stamp} - STD {k}.log',
            ['Log', 'Out', 'Err']
        )

        rel_run_log_folder = f'json_dicts/{app_name} - {log_time_stamp}'

        if not os.path.exists(f'{tool_dir}/{rel_run_log_folder}'):
            os.makedirs(f'{tool_dir}/{rel_run_log_folder}')
        if not os.path.exists(f'{tool_dir}/{rel_artifact_folder}'):
            os.makedirs(f'{tool_dir}/{rel_artifact_folder}')

        json_file_name = f'{app_name} - {log_time_stamp}.json'
        with open(f'{tool_dir}/{rel_run_log_folder}/{json_file_name}', 'w') as f:
            f.write(nl_project_manager_selection)

        command_list = [
            'python',
            f'{tool_dir}/workflow.py',  # file Name
            app_name,  # 1 App name ##IAD
            tool_dir,  # 2 tool directory to change CW directory ## neoload_project_manager\the_tool
            rel_run_log_folder,
            # 3 Relative to tools directory for run logs After Changed directory # json_dicts\REM - Oct 12, 2020 at 10-12-39 PM
            json_file_name,  # 4 json file name to merge later in path  # REM - Oct 12, 2020 at 10-12-39 PM.json
            std_log_file_name,  # 5 REM - Oct 12, 2020 at 10-12-39 PM - STD Log.log
            std_out_file_name,  # 6 REM - Oct 12, 2020 at 10-12-39 PM - STD Out.log
            std_err_file_name,  # 7 REM - Oct 12, 2020 at 10-12-39 PM - STD Err.log
        ]

        subprocess.Popen(command_list)
        context = {
            # Path of the File From Current Directory
            'run_log_file': f'{tool_dir}/{rel_run_log_folder}/{std_log_file_name}',
            'std_out_file': f'{tool_dir}/{rel_run_log_folder}/{std_out_file_name}',
            'std_err_file': f'{tool_dir}/{rel_run_log_folder}/{std_err_file_name}',
        }
        # print('context', context)
        return render(request, 'main_page/run_tracker.html', context=context)

    if run_tool == 'nl_test_starter':
        nl_test_starter_selection = request.POST.get('nl_test_starter_selection')

        tool_dir = 'nl_test_starter/the_tool'

        std_log_file_name, std_out_file_name, std_err_file_name = map(
            lambda k: f'{app_name} - {log_time_stamp} - STD {k}.log',
            ['Log', 'Out', 'Err']
        )

        rel_run_log_folder = f'json_dicts/{app_name} - {log_time_stamp}'

        if not os.path.exists(f'{tool_dir}/{rel_run_log_folder}'):
            os.makedirs(f'{tool_dir}/{rel_run_log_folder}')
        if not os.path.exists(f'{tool_dir}/{rel_artifact_folder}'):
            os.makedirs(f'{tool_dir}/{rel_artifact_folder}')

        json_file_name = f'{app_name} - {log_time_stamp}.json'
        with open(f'{tool_dir}/{rel_run_log_folder}/{json_file_name}', 'w') as f:
            f.write(nl_test_starter_selection)

        command_list = [
            'python',
            f'{tool_dir}/workflow.py',  # file Name
            app_name,  # 1 App name ##IAD
            tool_dir,  # 2 tool directory to change CW directory ## neoload_project_manager\the_tool
            rel_run_log_folder,
            # 3 Relative to tools directory for run logs After Changed directory # json_dicts\REM - Oct 12, 2020 at 10-12-39 PM
            json_file_name,  # 4 json file name to merge later in path  # REM - Oct 12, 2020 at 10-12-39 PM.json
            std_log_file_name,  # 5 REM - Oct 12, 2020 at 10-12-39 PM - STD Log.log
            std_out_file_name,  # 6 REM - Oct 12, 2020 at 10-12-39 PM - STD Out.log
            std_err_file_name,  # 7 REM - Oct 12, 2020 at 10-12-39 PM - STD Err.log
        ]

        subprocess.Popen(command_list)
        context = {
            # Path of the File From Current Directory
            'run_log_file': f'{tool_dir}/{rel_run_log_folder}/{std_log_file_name}',
            'std_out_file': f'{tool_dir}/{rel_run_log_folder}/{std_out_file_name}',
            'std_err_file': f'{tool_dir}/{rel_run_log_folder}/{std_err_file_name}',
        }
        # print('context', context)
        return render(request, 'main_page/run_tracker.html', context=context)


def helper_db(request):
    global local_db_vars
    if request.method == 'POST':
        req_dict = dict()
        for k in request.POST:
            req_dict[k] = request.POST[k]
        del req_dict['csrfmiddlewaretoken']
        local_db_vars = DotMap(req_dict)

        with sqlite3.connect('helper.db') as conn:
            cursor = conn.cursor()
            for key, value in req_dict.items():
                cursor.execute('update helper_variables set PARAM_VALUE = :PARAM_VALUE where PARAM_NAME = :PARAM_NAME',
                               {'PARAM_VALUE': value, 'PARAM_NAME': key})
            conn.commit()
        conn.close()
        return redirect('plab-home')
    else:
        context = local_db_vars.toDict()
        context = {'params': context}
        return render(request, 'main_page/helperDB.html', context=context)


def run_tracker(request):
    is_refresh = request.POST.get('is_refresh')
    # print(request)
    # print(request.POST)
    # print(request.POST.get('std_out_file'))

    std_out_file = request.POST.get('std_out_file')
    std_err_file = request.POST.get('std_err_file')
    run_log_file = request.POST.get('run_log_file')

    std_out_length = int(request.POST.get('std_out_length'))
    std_err_length = int(request.POST.get('std_err_length'))
    run_log_length = int(request.POST.get('run_log_length'))

    print(std_out_file, std_err_file, run_log_file)

    with open(std_out_file, 'r') as f:
        data_lines = f.readlines()[std_out_length:]
        std_out_cont, std_out_length = ''.join(data_lines), len(data_lines) + std_out_length

    with open(std_err_file, 'r') as f:
        data_lines = f.readlines()[std_err_length:]
        std_err_cont, std_err_length = ''.join(data_lines), len(data_lines) + std_err_length

    with open(run_log_file, 'r') as f:
        data_lines = f.readlines()[run_log_length:]
        run_log_cont, run_log_length = ''.join(data_lines), len(data_lines) + run_log_length

    data = {
        'std_out_cont': std_out_cont,
        'std_err_cont': std_err_cont,
        'run_log_cont': run_log_cont,
        'std_out_length': std_out_length,
        'std_err_length': std_err_length,
        'run_log_length': run_log_length,
    }

    if is_refresh == 'True':
        return HttpResponse(json.dumps(data))
    else:
        return redirect('main-page-run-tracker')
