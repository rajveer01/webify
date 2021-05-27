import gps
import cx_Oracle
import all_loggers


def get():
    try:
        all_loggers.logger_log.info(f'''enter into get() function for DB snapshot IDs for 
    test start:    {gps.test_start_time}, 
    test stop:    {gps.test_stop_time}''')

        test_start = gps.test_start_time
        test_stop = gps.test_stop_time

        # sql_query1 = '''select SNAP_ID, END_INTERVAL_TIME from DBA_HIST_SNAPSHOT where
        # END_INTERVAL_TIME > (CURRENT_DATE -4) ORDER BY END_INTERVAL_TIME DESC'''
        sql_query = '''select SNAP_ID, END_INTERVAL_TIME from DBA_HIST_SNAPSHOT where 
        END_INTERVAL_TIME > (CURRENT_DATE -4) ORDER BY END_INTERVAL_TIME'''

        cs = f'{gps.schema_name}/{gps.schema_pwd}@{gps.db_IP}:{gps.oracle_db_port}/{gps.oracle_db_id}'

        start_id, stop_id = 0, 0

        all_loggers.logger_log.info(f'Trying to connect to ORACLE db with connection string: {cs}')
        all_loggers.logger_log.info(f'Will search timestamps for test start@ {test_start} and end@ {test_stop}')

        dsn_tns = cx_Oracle.makedsn(gps.db_IP, gps.oracle_db_port, service_name=gps.oracle_db_id)

        with cx_Oracle.connect(user=gps.schema_name, password=gps.schema_pwd, dsn=dsn_tns) as conn:
            with conn.cursor() as cursor:
                all_loggers.logger_log.info('Connected')
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                all_loggers.logger_log.info('Fetched data for Snapshot IDs')
                all_loggers.logger_log.info(f'rows1 fetch from db:{rows}')

        for row in rows:
            if row[1] <= test_start:
                start_id = row[0]

            stop_id = row[0]
            if row[1] > test_stop:
                break

        all_loggers.logger_log.info(f'Got start({start_id}) and stop({stop_id}) ids')
        return start_id, stop_id
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise e
