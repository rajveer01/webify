import all_loggers
import gps
import pandas as pd
import paramiko
import unicodedata
from paramiko import SSHClient
from datetime import datetime as dt
import re
from math import ceil
from datetime import timedelta


def get_user_rampup_time(item):
    pattern1 = re.compile(r'The population (.*?) is (ramp up from (\d+) users adding' +
                          r' (\d+) users every (\d+[.]\d+) (seconds|minutes|hours)),' +
                          r' to a maximum of (\d+) users')
    pattern2 = re.compile(r'The population (.*?) is (constant) with (\d+) users')

    if pattern1.match(item):
        pop_name, policy, starting, adding, after, time_quantifier, users = [float(k) if gps.is_float(k) else k for k in
                                                                             pattern1.findall(item)[0]]
        effective_users = 0 if 'health_report' in pop_name.strip().lower().replace(' ', '_') else users
        moments = ceil((users - starting) / adding) * after
        rampup_time = timedelta(**{time_quantifier: moments}).total_seconds()
        return {'users': effective_users, 'rampup_time': rampup_time, 'policy': policy}

    elif pattern2.match(item):
        pop_name, policy, users = [float(k) if gps.is_float(k) else k for k in pattern2.findall(item)[0]]
        effective_users = 0 if 'health_report' in pop_name.strip().lower().replace(' ', '_') else users
        rampup_time = 0
        return {'users': effective_users, 'rampup_time': rampup_time, 'policy': policy}
    return {'users': 0, 'rampup_time': 0, 'policy': 'Unmatched'}


def get_times(summary_file):
    try:
        tables = pd.read_html(summary_file)

        all_loggers.logger_log.info(f'trying to get the latest times from {summary_file}')

        start = dt.strptime(str(tuple(tables[0][4:5].get(1))[0]), '%b %d, %Y %I:%M:%S %p')
        stop = dt.strptime(str(tuple(tables[0][5:6].get(1))[0]), '%b %d, %Y %I:%M:%S %p')

        pop_stmt_s = unicodedata.normalize('NFKD', tables[0][3][2]).split('. ')
        pop_stmt_s_dict = [{**{'statement': i.strip()}, **get_user_rampup_time(i)} for i in pop_stmt_s]

        gps.number_of_users_in_test = sum([i['users'] for i in pop_stmt_s_dict])
        gps.rampup_time_secs = max([i['rampup_time'] for i in pop_stmt_s_dict])

        # Getting Avg Pages/s, Req/s, Avg Throughput
        gps.avg_pages_ps = tables[1][4][0]
        gps.avg_req_s_ps = tables[1][4][1]
        gps.avg_throughput_ps = tables[1][4][4]
        gps.avg_txn_rt = tables[13]['Avg'][1]

        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # print(f"gps.db_IP, gps.user, gps.DB_Oracle_PWD, {gps.db_IP}, {gps.user}, {gps.DB_Oracle_PWD}")
        ssh.connect(gps.db_IP, port=22, username=gps.user, password=gps.DB_Oracle_PWD)
        _, output, _ = ssh.exec_command('date')
        db_time = output.read().decode().strip()

        _, output, _ = ssh.exec_command('date +"%Z"')
        gps.db_zone = output.read().decode().strip()
        db_time = dt.strptime(str(db_time).replace(gps.db_zone, ''), '%a %b %d %H:%M:%S  %Y')

        lts = dt.now()

        cmd = '''date /t && echo %time%'''
        raw_list = gps.rce.run_executable("cmd.exe", arguments=f"/c {cmd}")[0].decode().splitlines()

        all_loggers.logger_log.info(f'Date times for windows machine : raw List : {raw_list}')
        win_time = dt.strptime(''.join(raw_list), '%a %m/%d/%Y %H:%M:%S.%f')
        all_loggers.logger_log.info(f"win_time: {win_time}")
        lte = dt.now()

        win_time = win_time - ((lte - lts) / 2)
        all_loggers.logger_log.info(f"New windows Time {win_time}")

        ssh.close()
        time_dif = win_time - db_time

        all_loggers.logger_log.info(f'''Time Difference Between windows({win_time}) 
        and DB({db_time}) is {time_dif.total_seconds() / 3600} hrs''')

        start = start - time_dif
        stop = stop - time_dif

        gps.test_start_time = start
        gps.test_stop_time = stop

        all_loggers.logger_log.info(f'test start time {start} and stop time {stop}')
        return start, stop
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
