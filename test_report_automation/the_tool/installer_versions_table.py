import all_loggers
import xml.etree.ElementTree as Et

import cx_Oracle
import gps


def get_table():
    try:
        all_loggers.logger_log.info('Get table function has been called.')
        table = Et.Element('table', cellpadding='1', style="text-align:center;  font-family: Calibri")
        Et.SubElement(table, 'style').text = 'table, th, td {border:1px solid black;}'
        tr = Et.SubElement(table, 'tr', style='background-color: rgb(91, 155, 213); color: white; font-weight: bold;')

        Et.SubElement(tr, 'th').text = 'Module Name'
        Et.SubElement(tr, 'th').text = 'Installer Name'
        Et.SubElement(tr, 'th').text = 'Version'

        cs = f'{gps.schema_name}/{gps.schema_pwd}@{gps.db_IP}:{gps.oracle_db_port}/{gps.oracle_db_id}'

        all_loggers.logger_log.info(f'Connecting to oracle db with CS : {cs}')

        dsn_tns = cx_Oracle.makedsn(gps.db_IP, gps.oracle_db_port, service_name=gps.oracle_db_id)

        with cx_Oracle.connect(user=gps.schema_name, password=gps.schema_pwd, dsn=dsn_tns) as conn:
            with conn.cursor() as cursor:
                query = '''
                SELECT MODULE_NAME, INSTALLER_NAME, VERSION FROM SI_VERSION_INFO WHERE INSTALLER_ID IN 
                (SELECT MAX(INSTALLER_ID) FROM SI_VERSION_INFO GROUP BY Module_name) AND 
                MODULE_NAME NOT IN({avoid_me}) 
                ORDER BY MODULE_NAME
                '''

                installers = gps.installers_to_avoid
                avoid_me = "'dummy"
                for installer in installers:
                    if len(installer.strip()) > 0:
                        avoid_me += "','" + installer.strip()
                avoid_me += "'"
                all_loggers.logger_log.info(f'Executing the query: {query.format(avoid_me=avoid_me)}')
                cursor.execute(query.format(avoid_me=avoid_me))
                rows = cursor.fetchall()
                for row in rows:
                    tr = Et.SubElement(table, 'tr')
                    Et.SubElement(tr, 'td').text = row[0]
                    Et.SubElement(tr, 'td').text = row[1]
                    Et.SubElement(tr, 'td').text = row[2]
                all_loggers.logger_log.info('installer versions table generated')
                return table
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
