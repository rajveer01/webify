from datetime import datetime as dt
import json
import os
import subprocess
import traceback
import all_loggers
import smtplib

import paramiko
import svn.remote
from paramiko import SSHClient
import requests

import cx_Oracle
import nl_txn_name_finder
import gps

# todo add Logging, Add Execution and Monitor Project checks.


def validate():
    try:
        any_failed = []

        # Do TXNs have JSON desc
        nl_txn_name_finder.get_dict()

        # if mail is accessible
        try:
            with smtplib.SMTP('qatools.metricstream.com', 25) as smtp:
                smtp.close()
        except Exception as e:
            all_loggers.logger_log.exception(e)

        # If neoload Execution Project is available

        data = {"d": {}}
        data = json.dumps(data)
        headers = {"Content-type": "application/json"}

        url_g = f"http://{gps.execution_IP}:7400/Runtime/v1/Service.svc/GetStatus"
        resp = requests.post(url_g, data=data, headers=headers)
        if resp.status_code != 201:
            any_failed.append(f"Execution Machine's {gps.execution_IP} Neoload is not Accessible")

        # If neoload Execution Project is available
        # if gps.monitor_available:
        #     url_g = "http://%s:7400/Runtime/v1/Service.svc/GetStatus" % gps.monitor_IP
        #     resp = requests.post(url_g, data=data, headers=headers)
        #     if resp.status_code != 201:
        #         any_failed.append('Monitor Machine\'s {} Neoload is not Accessible'.format(gps.execution_IP))

        # Check If monitor ip, execution ip pingable

        # if gps.monitor_available:
        #     if subprocess.call('ping -n 1 %s' % gps.monitor_IP, stdout=subprocess.PIPE):
        #         any_failed.append('Monitor IP {} not accessible'.format(gps.monitor_IP))
        if subprocess.call('ping -n 1 %s' % gps.execution_IP, stdout=subprocess.PIPE):
            any_failed.append(f'Execution IP {gps.execution_IP} not accessible')

        '''svn client connectible for op and Artifact Location'''
        client = svn.remote.RemoteClient(url=gps.svn_artifact_folder,
                                         username=gps.svn_user_name,
                                         password=gps.svn_password)
        try:
            client.info()
        except Exception as e:
            any_failed.append(f'UnSuccessful SVN connection for artifacts folder {e} \n {traceback.format_exc()}')

        client = svn.remote.RemoteClient(url=gps.svn_op_location, username=gps.svn_user_name, password=gps.svn_password)
        try:
            client.info()
        except Exception as e:
            any_failed.append(f'Not Successful SVN connection for OP {e} \n {traceback.format_exc()}')

        '''combination of app_name run number script version and Release name do not exist
        If compare with old is true, Old test params do exist'''

        with cx_Oracle.connect(gps.oracle_db_cs) as conn:
            with conn.cursor() as cursor:
                query = '''
                SELECT COUNT(*) AS RECS FROM PT_RESULTS WHERE APP_NAME = :APP_NAME AND TEST_RUN_NO = :TEST_RUN_NO AND
                 RELEASE_NAME = :RELEASE_NAME AND TEST_TYPE = :TEST_TYPE
                '''
                query_f_current = {'APP_NAME': gps.app_name, 'TEST_RUN_NO': gps.run,
                                   'RELEASE_NAME': gps.release_name, 'TEST_TYPE': gps.test_type}
                query_f_old = {'APP_NAME': gps.app_name, 'TEST_RUN_NO': gps.old_run,
                               'RELEASE_NAME': gps.old_release_name, 'TEST_TYPE': gps.old_test_type}
                cursor.execute(query, query_f_current)
                row_current = cursor.fetchone()
                if gps.compare_with_old:
                    cursor.execute(query, query_f_old)
                    row_old = cursor.fetchone()

        if row_current[0] != 0:
            any_failed.append('New Run Param: combination (app_name, run, test type and Release name) not unique')
        if gps.compare_with_old:
            if row_old[0] == 0:
                any_failed.append('Old run Param: combination (run number and Release name is missing')

        '''db for app is connectible'''
        _ = f'{gps.schema_name}/{gps.schema_pwd}@{gps.db_IP}:{gps.oracle_db_port}/{gps.oracle_db_id}'

        dsn_tns = cx_Oracle.makedsn(gps.db_IP, gps.oracle_db_port, service_name=gps.oracle_db_id)

        try:
            with cx_Oracle.connect(user=gps.schema_name, password=gps.schema_pwd, dsn=dsn_tns) as conn:
                if conn:
                    pass
        except Exception as e:
            any_failed.append(f'Not Successful ORACLE DB connection with {e} \n {traceback.format_exc()}')

        '''app server and db server are connectible through ssh'''

        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(gps.app_IP, port=22, username=gps.user, password=gps.App_Oracle_PWD)
            ssh.close()
        except Exception as e:
            any_failed.append(f'Connection Failed {gps.app_IP}:22@{gps.user}/{gps.App_Oracle_PWD}, {e}\n {traceback.format_exc()}')

        try:
            ssh.connect(gps.db_IP, port=22, username=gps.user, password=gps.DB_Oracle_PWD)
            ssh.close()
        except Exception as e:
            any_failed.append(f'Connection Failed {gps.db_IP}:22@{gps.user}/{gps.DB_Oracle_PWD}, {e} \n {traceback.format_exc()}')

        ''' Project folder do exist'''
        if not os.path.exists(gps.execution_project_folder):
            any_failed.append('Project Folder do not Exists')

        if not os.path.exists(os.path.join(gps.execution_project_folder, 'config.zip')):
            any_failed.append('Config file do not Exist in Project Folder')

        if not os.path.exists(os.path.join(gps.execution_project_folder, 'results')):
            any_failed.append('Results folder do not Exist in Project Folder')

        ''' Artifact folder do exists'''
        if not os.path.exists(gps.artifacts_folder):
            any_failed.append('Artifacts folder do not Exist {}'.format(gps.artifacts_folder))

        ''' total users mentioned is number only'''
        if gps.total_users.upper() != 'NA':
            if not gps.is_float(gps.total_users):
                any_failed.append('Total user {} in case of 100% load in not a Number or NA'.format(gps.total_users))

        ''' execution time and DB times are same'''

        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(gps.db_IP, port=22, username=gps.user, password=gps.DB_Oracle_PWD)
        _, output, _ = ssh.exec_command('date')

        # lts = dt.now()
        cmd = '''date /t && echo %time%'''
        raw_list = gps.rce.run_executable("cmd.exe", arguments=f"/c {cmd}")[0].decode().splitlines()
        # # ['Mon 07/27/2020 ','13:12:44.42']
        # win_time = dt.strptime(''.join(raw_list), '%a %m/%d/%Y %H:%M:%S.%f')
        # lte = dt.now()
        # win_time = win_time - ((lte - lts) / 2)
        #
        # db_time = output.read().decode().strip()
        # _, output, _ = ssh.exec_command('date +"%Z"')
        # db_zone = output.read().decode().strip()
        # ssh.close()
        # db_time = dt.strptime(str(db_time).replace(db_zone, ''), '%a %b %d %H:%M:%S  %Y')
        # time_dif = win_time - db_time
        # gps.time_diff_bwn_exec_db = time_dif
        # time_dif = round(time_dif.total_seconds()/60)
        # if time_dif != 0:
        #     print('Time is different in DB and Windows Machine by {} minutes'.format(time_dif))
        if len(any_failed) != 0:
            all_loggers.logger_log.info(f"any_failed: {any_failed}")
            x = '\n .1. '.join(any_failed)
            raise Exception('\n .1. Prerequisite failed with below %s' % x)
    except Exception as e:
        raise e
    else:
        return gps
    finally:
        pass