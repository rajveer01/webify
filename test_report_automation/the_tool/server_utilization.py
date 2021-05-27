import all_loggers
import xml.etree.ElementTree as Et
import pandas as pd
import os
import zipfile

import paramiko
from paramiko import SSHClient

import gps


def get_monitoring_host_infra():
    project_path = gps.execution_project_folder + r"\config.zip"
    all_loggers.logger_log.info(f'Entered the Get_dict() function for reading the config.zip file: {project_path}')
    with zipfile.ZipFile(project_path) as archive:
        repo_file = archive.read("repository.xml")
        archive.close()
    all_loggers.logger_log.info('Zip file reading completed. For Monitoring Hosts')
    tree = Et.ElementTree(Et.fromstring(repo_file))
    root = tree.getroot()
    monitored_hosts = root.findall("monitored-host")
    monitored_hosts_list = [
        {
            'monitor_name': host.attrib['uid'],
            'monitor_ip': host.attrib['host-name']
        }
        for host in monitored_hosts
    ]
    all_loggers.logger_log.info(f'''Got Monitored hosts Tuple as Without infra 
{monitored_hosts_list}
''')

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # todo Change the Port and Credential for Monitoring Hosts Here
    for host_tuple in monitored_hosts_list:
        ssh.connect(host_tuple['monitor_ip'], port=22, username='oracle', password='oracle')
        all_loggers.logger_log.info(f"Opened SSH{host_tuple['monitor_name']} for core and memory with {host_tuple['monitor_ip']}")
        _, out, _ = ssh.exec_command('nproc')
        cores = str(out.readlines()[0].strip())
        ram = int(cores) * 4
        ssh.close()
        all_loggers.logger_log.info(f'Got cores: {cores}) and ram: {ram} in {host_tuple["monitor_name"]}')
        host_tuple['cores'] = cores.__str__()
        host_tuple['ram'] = ram.__str__()
    all_loggers.logger_log.info(f'''Returning monitored_hosts_list as 
{monitored_hosts_list}
''')
    return monitored_hosts_list


def get_utilization():
    monitored_hosts_list = get_monitoring_host_infra()
    '''Design For monitored_hosts_list
    [{
        'monitor_name': 'BCM_APP',
        'monitor_ip': '10.100.1.219',
        'cores': '4'
        'ram': '16'
    }]
    '''

    summary_folder_in_latest_folder = os.path.dirname(gps.index_from_res_path)
    monitors_html_file = os.path.join(summary_folder_in_latest_folder, 'index_files/monitors.html')
    data = pd.read_html(monitors_html_file)

    for host in monitored_hosts_list:
        monitor_name = host['monitor_name']
        monitor_ip = host['monitor_ip']
        cores = host['cores']
        ram = host['ram']

        avg_cpu_usr = ''
        avg_cpu_sys = ''
        max_mem_tot = ''
        max_mem_use = ''

        for i in range(len(data)):
            df = data[i]
            ''' df here is a Data frame, means one Table in HTML'''
            rows, _ = df.shape
            for k in range(rows):
                name = str(df[k:k + 1][0][k]).lower()
                try:
                    value1 = str(df[k:k + 1][1][k]).lower()
                except:
                    value1 = ''
                try:
                    value2 = str(df[k:k + 1][2][k]).lower()
                except:
                    value2 = ''
                try:
                    value3 = str(df[k:k + 1][3][k]).lower()
                except:
                    value3 = ''
                if f'{monitor_name}/Linux/System/CPU User'.lower() in name:
                    avg_cpu_usr = value2
                elif f'{monitor_name}/Linux/System/CPU System'.lower() in name:
                    avg_cpu_sys = value2
                elif f'{monitor_name}/Linux/Memory/Memory Total'.lower() in name:
                    max_mem_tot = value3
                elif f'{monitor_name}/Linux/Memory/Memory Used'.lower() in name:
                    max_mem_use = value3
                elif f'{monitor_name}/tomcat/java.lang/Threading/ThreadCount'.lower() in name:
                    gps.tc_thread_count = value2
                elif f'{monitor_name}/oracleDB/Logical IO/Block changes'.lower() in name:
                    gps.logical_blocks = value2

        try:
            cpu_utilization = round(float(avg_cpu_usr) + float(avg_cpu_sys), 2).__str__()
        except:
            cpu_utilization = 'NA'
        try:
            mem_utilization = round(float(max_mem_use) * 100 / float(max_mem_tot), 2).__str__()
        except:
            mem_utilization = 'NA'

        host['cpu_utilization'] = cpu_utilization
        host['mem_utilization'] = mem_utilization

    '''Design For monitored_hosts_list
    [{
        'monitor_name': 'BCM_APP',
        'monitor_ip': '10.100.1.219',
        'cores': '4',
        'ram': '16',
        'cpu_utilization': '46',
        'mem_utilization': '50',
    }]
    '''

    '''making Format for compatibility'''
    formatted_monitored_hosts_list = []
    for host in monitored_hosts_list:
        # formatting formatted List
        temp_cpu = (host['cpu_utilization'], f"{host['monitor_name']} CPU", host['cores'])
        temp_mem = (host['mem_utilization'], f"{host['monitor_name']} Memory", host['ram'])
        formatted_monitored_hosts_list.append(temp_cpu)
        formatted_monitored_hosts_list.append(temp_mem)

        # setting gps ' s
        if 'app' in host['monitor_name'].lower():
            gps.app_cores = host['cores']
            gps.app_ram = host['ram']
            gps.app_cpu_util = host['cpu_utilization']
            gps.app_mem_util = host['mem_utilization']
        elif 'db' in host['monitor_name'].lower():
            gps.db_cores = host['cores']
            gps.db_ram = host['ram']
            gps.db_cpu_util = host['cpu_utilization']
            gps.db_mem_util = host['mem_utilization']

    all_loggers.logger_log.info(f'monitored_hosts_list: {monitored_hosts_list}')
    all_loggers.logger_log.info(f'formatted_monitored_hosts_list: {formatted_monitored_hosts_list}')
    return monitored_hosts_list

'''
# Old Function
def old_get_utilization(monitor_ip=gps.monitor_IP):
    try:
        all_loggers.logger_log.info('Entered into the get_utilization() function with Monitor IP as {}'.format(monitor_ip))

        url_g = "http://%s:7400/Results/v1/Service.svc/GenerateReport" % monitor_ip
        url_d = "http://%s:7400/Results/v1/Service.svc/DownloadReport" % monitor_ip

        all_loggers.logger_log.info('Generating the Monitor report in XML format with {}'.format(url_g))

        data = {"d": {"Format": "XML"}}                                #
        data = json.dumps(data)                                        # Generate
        headers = {'Content-type': 'application/json'}                 # And
        resp = requests.post(url_g, data=data, headers=headers)        # Download
        repid = json.loads(resp.text)['d']['ReportId']                 # the Reports

        all_loggers.logger_log.info('generate NL Report Executed with response code {} and response{}\n and got report id {}'.format(
            resp.status_code, resp.text, repid))

        data = {"d": {"ReportId": repid}}                              # Here.
        data = json.dumps(data)                                        # In XML Format
        resp = requests.post(url_d, data=data, headers=headers)        #
        while not str(resp.status_code) == '201':                      #
            all_loggers.logger_log.info("Wait for {} to generate the report, status: {}, response:{}".format(monitor_ip,
                                                                                              resp.status_code,
                                                                                              resp.text))
            resp = requests.post(url_d, data=data, headers=headers)    #
            time.sleep(3)                                              #

        all_loggers.logger_log.info('Parsing the Response as XML')

        tree = Et.ElementTree(Et.fromstring(resp.text))                                          # Parse
        root = tree.getroot()                                                                    # The Downloaded
        monitored_hosts = root.findall('./monitors/monitored-host[@monitor-agent="localhost"]')  # Report into XML

        list_of_utils = []
        for monitored_host in monitored_hosts:
            for monitor in monitored_host:
                if "Linux".upper() in str(monitor.attrib['name']).upper():
                    for tag_in_monitor in monitor:
                        if tag_in_monitor.tag == "counters":
                            cpu_util = 0
                            cpu_util_name = ""
                            mem_util = 0
                            mem_util_name = ""
                            for statistic_item in tag_in_monitor:
                                name_of_item = str(statistic_item.attrib['name'])
                                # cpu util
                                if "System/CPU User".upper() in name_of_item.upper():
                                    cpu_util += float(statistic_item.attrib['avg'])
                                    cpu_util_name = name_of_item.split(" User")[0]
                                if "System/CPU System".upper() in name_of_item.upper():
                                    cpu_util += float(statistic_item.attrib['avg'])
                                # memory util
                                if "Memory/Memory Total".upper() in name_of_item.upper():
                                    mem_util = float(str(statistic_item.attrib['max']).replace(',', ''))
                                    mem_util_name = name_of_item.split("/Memory Total")[0]
                                if "Memory/Memory Used".upper() in name_of_item.upper():
                                    used = float(str(statistic_item.attrib['max']).replace(',', ''))
                                    if mem_util != 0:
                                        mem_util = (used * 100) / mem_util
                            fancy_key = cpu_util_name.split('/', 1)[0]
                            cores, ram = get_infra_from_fancy_key(fancy_key)
                            list_of_utils.append((str(cpu_util.__round__(2)), cpu_util_name, cores))
                            list_of_utils.append((str(mem_util.__round__(2)), mem_util_name, ram))

        all_loggers.logger_log.info('got utilisation as :')
        all_loggers.logger_log.info(list_of_utils)

        return list_of_utils
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
'''


"""
# old function

def get_infra_from_fancy_key(fancy_key):
    try:
        all_loggers.logger_log.info('trying to connect for the fancy Key {} IPs'.format(fancy_key))
        temp = '''SELECT IP, user_name, password FROM PLAB_SERVERS_FANCY_KEYS_T WHERE
        UPPER(F_Key) = UPPER('{F_Key}')'''.format(F_Key=fancy_key.replace(' ', '_'))
        gps.global_cursor.execute(temp)
        ip, user, password = gps.global_cursor.fetchone()

        all_loggers.logger_log.info('Fetched one record from fancy key table as IP: {}, user: {}, PWD: {}'.format(ip, user, password))

        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=22, username=user, password=password)
        all_loggers.logger_log.info('Opened SSH for core and memory with {}'.format(ip))
        inn, outt, err = ssh.exec_command('nproc')
        cores = str(outt.readlines()[0].strip())

        # inn, outt, err = ssh.exec_command('cat /proc/meminfo | grep MemTotal: ')
        # temp = str(outt.readlines()[0].strip())
        # ram = temp.split(':', 1)[1].split('kB', 1)[0].strip()
        # ram = (int(ram)/1024)/1024
        # from math import ceil as ru
        # ram = 4 * ru(ram / 4)
        ram = int(cores) * 4
        ssh.close()
        all_loggers.logger_log.info('Got cores({}) and ram({})'.format(str(cores), str(ram)))
        return str(cores), str(ram)
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
"""