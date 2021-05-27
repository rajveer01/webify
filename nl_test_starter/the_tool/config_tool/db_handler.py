import math
import cx_Oracle
import time
import all_loggers
from datetime import datetime as dt


logging = all_loggers.logger_log


def db_handler(file, ssh_db, ssh_db_root, sftp_db, db_ram, schema, schema_psw, db_port, sid, db_ip):
    SCHEMA = schema
    PASSWORD = schema_psw
    DB_IP = db_ip
    DB_PORT = db_port
    SID = sid
    with sftp_db.open(file) as f:  # opening init.ora file
        lines = f.readlines()
        new_lines = ''
        prev_val = ''
        mem = math.floor(int(db_ram) * 0.85)
        for line in lines:
            line_as_list = line.split('=', 1)
            if line_as_list[0].strip() in ('memory_max_target', 'memory_target'):
                prev_val = line_as_list[1]
                line_as_list[1] = mem
                line = line_as_list[0] + '= ' + str(line_as_list[1]) + 'G\n'
            new_lines += line
    logging.info(f"The memory_max_target and memory_target values are changed to : {mem}G")

    with sftp_db.open(file, 'wb') as f:
        f.write(new_lines)
        logging.info("Written file back to the DB")

    command_spfile = '''
    sqlplus / as 'sysdba' <<!
    create spfile from pfile='{file}';
    !'''.format(file=file)

    command_mount = f'mount -t tmpfs shmfs -o size={mem}G /dev/shm'

    start_oracle = '''
    sqlplus / as 'sysdba' <<!
    startup
    !'''

    start_pdb ='''
    sqlplus / as 'sysdba' <<!
    alter pluggable database pdb1 open;
    !'''

    db_shutdown = ''''
    sqlplus / as 'sysdba' <<!
    shutdown immediate
    !'''

    inn, out, err = ssh_db.exec_command(db_shutdown)
    out.channel.recv_exit_status()
    out.read()
    logging.info("Executed the Command to Shutdown the DB Services")

    inn, out, err = ssh_db.exec_command(command_spfile)
    out.channel.recv_exit_status()
    out.read()
    logging.info("Executed the Command to Create spfile")

    inn, out, err = ssh_db_root.exec_command(command_mount)
    out.channel.recv_exit_status()
    out.read()
    logging.info("Executed the Command for mounting the value")

    inn, out, err = ssh_db.exec_command(start_oracle)
    out.channel.recv_exit_status()
    out.read()
    logging.info("Executed the Command to start the DB Services")

    inn, out, err = ssh_db.exec_command(start_pdb)
    out.channel.recv_exit_status()
    out.read()
    logging.info("Executed the Command to start the PDB Services")

    inn, out, err = ssh_db.exec_command('lsnrctl start')
    out.channel.recv_exit_status()
    out.read()
    logging.info("Executed the Command to Start the DB Listener Services")

    ts_start, wait_time = dt.now(), 120
    logging.info(f'ts_start: {ts_start}')
    while True:
        logging.info(f'''
        started to wait at: {ts_start} 
        Now: {dt.now()}
        time passed: {(dt.now() - ts_start).total_seconds()}Secs of {wait_time} secs
        ''')
        time.sleep(1)
        try:
            dsn_tns = cx_Oracle.makedsn(DB_IP, DB_PORT, service_name=SID)
            with cx_Oracle.connect(user=SCHEMA, password=PASSWORD, dsn=dsn_tns) as _:
                logging.info('Connected!!! Breaking Loop')
                break
        except Exception as e:
            print(e)
            logging.info(f'{e} for {SCHEMA}/{PASSWORD}@{DB_IP}:{DB_PORT}/{SID}')
        if (dt.now() - ts_start).total_seconds() > wait_time:
            raise Exception(f'Wait time for Oracle DB({wait_time} sec) has expired.')

    print(f'{SCHEMA}/{PASSWORD}@{DB_IP}:{DB_PORT}/{SID}')

    dsn_tns = cx_Oracle.makedsn(DB_IP, DB_PORT, service_name=SID)
    conn = cx_Oracle.connect(user=SCHEMA, password=PASSWORD, dsn=dsn_tns)
    logging.info(f"Successfully Connected to DB Schema :{SCHEMA}")
    cursor = conn.cursor()
    sql = "select distinct LAST_ANALYZED from USER_TABLES where rownum = 1 order by LAST_ANALYZED desc"
    cursor.execute(sql)
    x = cursor.fetchall()
    logging.info("Successfully Executed the query and stored the result ")

    sql1 = '''select last_analyzed from dba_indexes where table_name='SI_USERS_T' 
    and rownum = 1 order by LAST_ANALYZED desc'''
    cursor.execute(sql1)
    y = cursor.fetchall()
    logging.info("Successfully Executed the query and stored the result ")

    try:
        db_result = x[0][0].strftime('%d-%b-%Y,%I:%M:%S')
        print('Gather Stats Date', x[0][0].strftime('%d-%b-%Y,%I:%M:%S'))

        idx_date = y[0][0].strftime('%d-%b-%Y,%I:%M:%S')
        print('Index Rebuild Date', y[0][0].strftime('%d-%b-%Y,%I:%M:%S'))

        cursor.close()
        conn.close()

        return prev_val, mem, db_result, idx_date
    except:
        print("No Data")

        cursor.close()
        conn.close()

        return prev_val, mem, 'No Data Found', 'No Data Found'
