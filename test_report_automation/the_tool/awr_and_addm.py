import all_loggers
import os
import time

import paramiko
from paramiko import SSHClient

import get_test_time as gtt
import gps
import db_snapshot_start_stop_id
import pb


def generate_and_copy():

    try:
        all_loggers.logger_log.info('Entered into generate_and_copy() function')
        test_start, test_stop = gtt.get_times(gps.index_from_res_path)
        print(pb.n.s_num, 'Got the Test Start & Stop Times')
        all_loggers.logger_log.info(f'Got times from {gps.index_from_res_path}, start: {test_start} stop: {test_stop}')

        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(gps.db_IP, port=22, username=gps.user, password=gps.DB_Oracle_PWD)

        _, out, _ = ssh.exec_command('''sqlplus / 'as sysdba'<<!
exec dbms_workload_repository.create_snapshot;
!''')
        out.channel.recv_exit_status()
        time.sleep(5)
        all_loggers.logger_log.info(f'''SSHed db to , {gps.schema_name}/{gps.schema_pwd}@{gps.db_IP} with
         test start:    {test_start},   stop:   {test_stop}''')

        start, end = db_snapshot_start_stop_id.get()

        print(pb.n.s_num, 'Got the Test Start & Stop DB Snapshots IDs')

        all_loggers.logger_log.info(f'Got Snapshot IDS as {start} and {end}')

        addm_name = f'{gps.app_name}_{gps.run_description.strip()}_ADDM_Report_{start}_{end}.txt'
        addm_name = addm_name.replace(' ', '_')
        awr_name = f'{gps.app_name}_{gps.run_description.strip()}_AWR_Report_{start}_{end}.html'
        awr_name = awr_name.replace(' ', '_')

        all_loggers.logger_log.info(f'Using ADDM name {addm_name}')
        all_loggers.logger_log.info(f'Using AWR name {awr_name}')

        command_for_addm_rpt = '''sqlplus / 'as sysdba'<<!
@%s/rdbms/admin/addmrpt.sql
%d
%d
%s/rdbms/admin/%s
!''' % (gps.db_home, start, end, gps.db_home, addm_name)

        command_for_awr_rpt = '''sqlplus / 'as sysdba'<<!
@%s/rdbms/admin/awrrpt.sql


%d
%d
%s/rdbms/admin/%s
!''' % (gps.db_home, start, end, gps.db_home, awr_name)

        all_loggers.logger_log.info(f'using the command for addm \n {command_for_addm_rpt}')
        all_loggers.logger_log.info(f'using the command for awr \n {command_for_awr_rpt}')

        addm_loc = f"{gps.db_home}/rdbms/admin/{addm_name}"
        awr_loc = f"{gps.db_home}/rdbms/admin/{awr_name}"

        print(pb.n.s_num, 'ADDM Report...')
        _, out, _ = ssh.exec_command(command_for_addm_rpt)
        all_loggers.logger_log.debug(out.read().decode())

        out.channel.recv_exit_status()
        all_loggers.logger_log.info(f"Check ADDM Report : {addm_loc} \n ")

        print(pb.n.s_num, 'AWR Report...')
        _, out, _ = ssh.exec_command(command_for_awr_rpt)
        all_loggers.logger_log.debug(out.read().decode())

        out.channel.recv_exit_status()
        all_loggers.logger_log.info(f"Check AWR Report : {awr_loc}")

        sftp = ssh.open_sftp()
        info1 = sftp.stat(awr_loc).st_size
        info2 = sftp.stat(addm_loc).st_size

        print(pb.n.s_num, 'Copying Reports...')
        while info1 <= 0 or info2 <= 0:
            all_loggers.logger_log.info(f'Checking the sizes of ADDM and AWR reports: {info1}, {info2}')
            info1 = sftp.stat(awr_loc).st_size
            info2 = sftp.stat(addm_loc).st_size
            time.sleep(4)

        all_loggers.logger_log.info(f'Sizes of ADDM and AWR reports: {info1}, {info2} are not Zero now.')
        sftp.get(awr_loc, os.path.join(gps.artifacts_folder, awr_name))
        sftp.get(addm_loc, os.path.join(gps.artifacts_folder, addm_name))

        all_loggers.logger_log.info(f'Copy Should have been successful ADDM and AWR reports: {info1}, {info2}')

        sftp.close()
        ssh.close()
        print(pb.n.s_num, 'AWR ADDM Reports Copied')
        return 'copy success'
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise e
