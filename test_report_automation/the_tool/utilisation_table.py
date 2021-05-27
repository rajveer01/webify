import all_loggers
import xml.etree.ElementTree as Et
import paramiko
from paramiko import SSHClient

import gps


def get_table(server_util_list):
    try:
        all_loggers.logger_log.info('Entered into get table method, Generating table now')

        table = Et.Element('table', cellpadding='5', style="text-align:center;  font-family: Calibri")
        Et.SubElement(table, 'style').text = 'table, th, td {border:1px solid black;}'
        tr = Et.SubElement(table, 'tr', style='background-color: rgb(91, 155, 213); color: white; font-weight: bold;')
        Et.SubElement(tr, 'th').text = 'Performance Counters'
        Et.SubElement(tr, 'th').text = 'Target Value'
        Et.SubElement(tr, 'th').text = 'Current Test'

        tr = Et.SubElement(table, 'tr')
        Et.SubElement(tr, 'td').text = '# of Concurrent Users'
        Et.SubElement(tr, 'td').text = f'{gps.total_users} '

        if gps.total_users.upper() != 'NA':
            Et.SubElement(tr, 'td').text = '{number_of_users_in_test} ( {load_perc} %)'.format(
                number_of_users_in_test=str(gps.number_of_users_in_test),
                load_perc=str(round(int(gps.number_of_users_in_test) * 100 / int(gps.total_users), 2)))
        else:
            Et.SubElement(tr, 'td').text = f'{gps.number_of_users_in_test}'

        tr = Et.SubElement(table, 'tr')

        Et.SubElement(tr, 'td').text = 'Workflow Per Minute (WPM)'
        if gps.wpm_matters:
            Et.SubElement(tr, 'td').text = f'{gps.wpm_required}'
            Et.SubElement(tr, 'td').text = f'{gps.wpm_achieve}'
        else:
            Et.SubElement(tr, 'td').text = f'{gps.wpm_required}'
            Et.SubElement(tr, 'td').text = 'NA'

        list_util_above_75 = []

        if gps.monitor_available:
            for util_row in server_util_list:
                tr = Et.SubElement(table, 'tr')
                Et.SubElement(tr, 'td').text = f'{util_row["monitor_name"]} CPU (Avg)'
                Et.SubElement(tr, 'td').text = '< 75%'
                if float(util_row['cpu_utilization']) >= 75:
                    Et.SubElement(tr, 'td', style='color:red; font-weight:bold;').text = f'''
                            {util_row["cpu_utilization"]}% ({util_row["cores"]} Cores)'''
                    list_util_above_75.append((util_row['monitor_name'], util_row['cpu_utilization']))
                else:
                    Et.SubElement(tr, 'td').text = f'{util_row["cpu_utilization"]}% ({util_row["cores"]} Cores)'

                tr = Et.SubElement(table, 'tr')
                Et.SubElement(tr, 'td').text = f'{util_row["monitor_name"]} Memory (Max)'
                Et.SubElement(tr, 'td').text = 'NA'
                Et.SubElement(tr, 'td').text = f'{util_row["mem_utilization"]}% ({util_row["ram"]} GB)'

            '''Old Way
            for util_row in server_util_list:
                tr = Et.SubElement(table, 'tr')
                if 'CPU'.upper() in str(util_row[1]).upper():
                    server_name = util_row[1].split('/')
                    server_name = server_name[0] + ' ' + server_name[-1]
                    Et.SubElement(tr, 'td').text = server_name + ' (Avg)'
                    Et.SubElement(tr, 'td').text = '< 75%'
                    if float(util_row[0]) >= 75:
                        Et.SubElement(tr, 'td', style='color:red; font-weight:bold;').text = util_row[0] + '% (' + util_row[2] + ' Cores)'
                        list_util_above_75.append((util_row[1], util_row[0]))
                    else:
                        Et.SubElement(tr, 'td').text = util_row[0] + '% (' + util_row[2] + ' Cores)'

                elif 'Memory'.upper() in str(util_row[1]).upper():
                    server_name = util_row[1].split('/')
                    server_name = server_name[0] + ' ' + server_name[-1]
                    Et.SubElement(tr, 'td').text = server_name + ' (Max)'
                    Et.SubElement(tr, 'td').text = 'NA'
                    Et.SubElement(tr, 'td').text = util_row[0] + '% (' + util_row[2] + 'GB)'
                
        else:  # Condition that Handles Table when Monitor Not Available.
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(gps.app_IP, port=22, username='oracle', password=gps.App_Oracle_PWD)
            all_loggers.logger_log.info(f'Opened SSH for core and memory with {gps.app_IP}')
            _, out, _ = ssh.exec_command('nproc')
            cores = str(out.readlines()[0].strip())
            ram = 4 * int(cores)
            ssh.close()
            all_loggers.logger_log.info(f'Got cores({cores}) and ram({ram})')
            app_core, app_memory = str(cores), str(ram)

            ssh.connect(gps.db_IP, port=22, username='oracle', password=gps.DB_Oracle_PWD)
            all_loggers.logger_log.info(f'Opened SSH for core and memory with {gps.db_IP}')
            _, out, _ = ssh.exec_command('nproc')
            cores = str(out.readlines()[0].strip())
            ram = 4 * int(cores)
            ssh.close()
            all_loggers.logger_log.info(f'Got cores({cores}) and ram({ram})')
            db_core, db_memory = str(cores), str(ram)

            tr = Et.SubElement(table, 'tr')
            Et.SubElement(tr, 'td').text = gps.app_name + ' App CPU(' + gps.app_IP + ')'
            Et.SubElement(tr, 'td').text = 'NA'
            Et.SubElement(tr, 'td').text = 'Cores : ' + app_core

            tr = Et.SubElement(table, 'tr')
            Et.SubElement(tr, 'td').text = gps.app_name + ' App Memory(' + gps.app_IP + ')'
            Et.SubElement(tr, 'td').text = 'NA'
            Et.SubElement(tr, 'td').text = 'Total Memory : ' + app_memory + ' GB'

            tr = Et.SubElement(table, 'tr')
            Et.SubElement(tr, 'td').text = gps.app_name + ' DB CPU(' + gps.db_IP + ')'
            Et.SubElement(tr, 'td').text = 'NA'
            Et.SubElement(tr, 'td').text = 'Cores : ' + db_core

            tr = Et.SubElement(table, 'tr')
            Et.SubElement(tr, 'td').text = gps.app_name + ' DB Memory(' + gps.db_IP + ')'
            Et.SubElement(tr, 'td').text = 'NA'
            Et.SubElement(tr, 'td').text = 'Total Memory : ' + db_memory + ' GB'
'''
        all_loggers.logger_log.info('Utilisation table has been generated.')
        return table, list_util_above_75
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise e
