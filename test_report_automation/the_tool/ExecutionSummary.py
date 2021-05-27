import paramiko
from paramiko import SSHClient
from datetime import datetime as dt
import gps

ssh_app = SSHClient()
ssh_app.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_app.connect('10.81.1.228', port=22, username='oracle', password='oracle')
pid = ssh_app.exec_command('ps a | less | grep Duser')[1].read().decode().split(' ', 1)[1].split(' ', 1)[0]
print(pid)
ssh_app.close()

'''THREAD DUMP'''
'''bash jstack_ThreadAutomate.sh 12895'''
'''MANUALLY'''

'''HEAP DUMP'''
jdk_location = '/data/jdk1.8.0_45/bin/jmap'
dump_directory = '/data/new_files/'
dump_name = 'heap_dump_%s.hprof' % str(dt.now().strftime('%Y-%m-%d_%H-%M-%S'))

dump_location = dump_directory + dump_name
heap_dump_command = jdk_location + ' -dump:live,format=b,file=' + dump_name + ' '+ pid

'''/data/jdk1.8.0_45/bin/jmap -dump:live,format=b,file=/data/new_files/heap_dump.hprof 6861'''

print(heap_dump_command)



import xml.etree.ElementTree as et
import os

xml_file = os.path.join(r'E:\New folder', "report-Jul-1-14_10.xml")

tree = et.parse(xml_file)
root = tree.getroot()

data_for_closure = dict()

'''EXECUTION'''
for child in root.iter('statistic'):
    #print(child.attrib['name']+'->'+ child.attrib['value']+child.attrib['unit'])
    data_for_closure[child.attrib['name']] = child.attrib['value']+child.attrib['unit']

for child in root.iter('rampuppolicy'):
    RAMP_UP_POLICY = 'From %s users, adding %s users  every %s%s, to a maximum of %s users.'%(child.attrib['from'], child.attrib['add'], child.attrib['interval'], child.attrib['unit'],child.attrib['max'])
    RAMP_UP_TIME = str(int((((int(child.attrib['max'])- int(child.attrib['from']))/int(child.attrib['add']))*float(child.attrib['interval']))/60))+' minutes and '+str(int((((int(child.attrib['max'])- int(child.attrib['from']))/int(child.attrib['add']))*float(child.attrib['interval']))%60))+' seconds'
    data_for_closure['RAMP_UP_TIME'] = RAMP_UP_TIME
    data_for_closure['RAMP_UP_POLICY'] = RAMP_UP_POLICY


'''MONITOR'''
xml_file = os.path.join(r'E:\New folder', "monitor.xml")

tree = et.parse(xml_file)
root = tree.getroot()

used_max = ''
used_total = ''

cpu_user = ''
cpu_system = ''

used_max_db = ''
used_total_db = ''

cpu_user_db = ''
cpu_system_db = ''

for child in root.iter('statistic-item'):
    if(child.attrib['name'] == 'Controller/Thread Count'):
        data_for_closure['THREAD_COUNT'] = child.attrib['avg']

    elif(child.attrib['name'] == 'FLN_DB/oracleDB/Logical IO/Block changes'):
        data_for_closure['LOGICAL_IO_BLOCK_CHANGES'] = child.attrib['avg']


    elif(child.attrib['name'] == 'FLN_APP/linux/Memory/Memory Used'):
        used_max= float(float(child.attrib['max'].replace(',',''))*100)
        # print(used_max)

    elif(child.attrib['name'] == 'FLN_APP/linux/Memory/Memory Total'):
        used_total = float(float(child.attrib['max'].replace(',','')))
        # print(used_total)

    elif(child.attrib['name'] == 'FLN_APP/linux/System/CPU User'):
        cpu_user = float(child.attrib['avg'])
        # print(cpu_user)

    elif(child.attrib['name'] == 'FLN_APP/linux/System/CPU System'):
        cpu_system = float(child.attrib['avg'])
        # print(cpu_system)

    elif (child.attrib['name'] == 'FLN_DB/Linux/Memory/Memory Used'):
        used_max_db = float(float(child.attrib['max'].replace(',', '')) * 100)
        # print(used_max_db)

    elif (child.attrib['name'] == 'FLN_DB/Linux/Memory/Memory Total'):
        used_total_db = float(float(child.attrib['max'].replace(',', '')))
        # print(used_total_db)

    elif (child.attrib['name'] == 'FLN_DB/Linux/System/CPU User'):
        cpu_user_db = float(child.attrib['avg'])
        # print(cpu_user_db)

    elif (child.attrib['name'] == 'FLN_DB/Linux/System/CPU System'):
        cpu_system_db = float(child.attrib['avg'])
        # print(cpu_system_db)


data_for_closure['APP_CORE_UTILIZED'] = cpu_system + cpu_user
data_for_closure['APP_MEM_UTILIZED'] = round(used_max/used_total,2)

data_for_closure['DB_CORE_UTILIZED'] = float(cpu_system_db) + float(cpu_user_db)
data_for_closure['DB_MEM_UTILIZED'] = round(used_max_db / used_total_db, 2)

for i,j in data_for_closure.items():
    print(i,j)


APP_NAME = gps.app_name
TEST_RUN_NO = gps.run
TEST_TYPE = gps.test_type
RELEASE_NAME = gps.release_name
TEST_DATE = gps.test_start_time
TEST_STATUS = ''#test_status_summary   #(report_automatiion line number 326)
LOAD_PERCENTAGE = int(round(int(gps.number_of_users_in_test) * 100 / int(gps.total_users), 2))
INSTALLERS = 'LIST OF INSTALLERS'
SCENARIOS_COUNT = 'line 271 scenarios_count_summary'
EXPECTED_WPM = gps.wpm_required
#ACTIVE_USERS = ACTIVE_USERS
CONCURRENT_USERS = gps.number_of_users_in_test

ssh = SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(gps.app_IP, port=22, username='oracle', password=gps.App_Oracle_PWD)
inn, outt, err = ssh.exec_command('nproc')
cores = str(outt.readlines()[0].strip())
ram = 4 * (cores)
ssh.close()
app_core, app_memory = str(cores), str(ram)

APP_CORE_ALLOCATED = app_core
APP_MEM_ALLOCATED = app_memory


ssh.connect(gps.db_IP, port=22, username='oracle', password=gps.DB_Oracle_PWD)
inn, outt, err = ssh.exec_command('nproc')
cores = str(outt.readlines()[0].strip())
ram = 4 * (cores)
ssh.close()
db_core, db_memory = str(cores), str(ram)

DB_CORE_ALLOCATED = db_core
DB_MEM_ALLOCATED = db_memory

APP_CORE_UTILIZED = data_for_closure['APP_CORE_UTILIZED']
APP_MEM_UTILIZED = data_for_closure['APP_MEM_UTILIZED']
DB_CORE_UTILIZED = data_for_closure['DB_CORE_UTILIZED']
DB_MEM_UTILIZED = data_for_closure['DB_MEM_UTILIZED']

ACHIEVED_WPM = gps.wpm_achieve
TOTAL_TRANSACTIONS = "total_txns_summary 345"
TOTAL_FAILED_TRANSACTIONS = "failed_txns_summary 345"
TEST_DURATION = str(gps.test_stop_time - gps.test_start_time)
THROUGHPUT = data_for_closure['avg_throughput']
HITS_PER_SEC = data_for_closure['avg_hits/s']
THREAD_COUNT = data_for_closure['THREAD_COUNT']
LOGICAL_IO_BLOCK_CHANGES = data_for_closure['LOGICAL_IO_BLOCK_CHANGES']
TEST_SCOPE = 'line 289 report automation  test_scope_summary'


changes_made_summary = '\n'.join(gps.changes_made)

CHANGES_MADE = changes_made_summary
REMARKS = ','.join(remarks_summary)
AVG_PAGE_PER_SEC = data_for_closure['avg_pages/s']
AVG_REQ_RESP_TIME = data_for_closure['avg_reqresponsetime']
RAMP_UP_TIME = data_for_closure['RAMP_UP_TIME']
SVN_PATH = gps.svn_artifact_folder
RAMP_UP_POLICY = data_for_closure['RAMP_UP_POLICY']
HEAP_DUMP_LOCATION = gps.heap_dump_location
THREAD_DUMP_LOCATION = gps.thread_dump_location

sql = '''
INSERT INTO TEST_EXECUTION_SUMMARY
(APP_NAME, TEST_RUN_NO, TEST_TYPE, RELEASE_NAME, TEST_DATE, TEST_STATUS, LOAD_PERCENTAGE, INSTALLERS, SCENARIOS_COUNT, 
EXPECTED_WPM, ACTIVE_USERS, CONCURRENT_USERS, APP_CORE_ALLOCATED, APP_MEM_ALLOCATED, DB_CORE_ALLOCATED, DB_MEM_ALLOCATED,
APP_CORE_UTILIZED, APP_MEM_UTILIZED, DB_CORE_UTILIZED, DB_MEM_UTILIZED, ACHIEVED_WPM, TOTAL_TRANSACTIONS,
  TOTAL_FAILED_TRANSACTIONS, TEST_DURATION, THROUGHPUT, HITS_PER_SEC, THREAD_COUNT, LOGICAL_IO_BLOCK_CHANGES, 
  TEST_SCOPE, CHANGES_MADE, REMARKS, AVG_PAGE_PER_SEC, AVG_REQ_RESP_TIME, RAMP_UP_TIME, SVN_PATH, RAMP_UP_POLICY, 
  ROW_ID, HEAP_DUMP_LOCATION, THREAD_DUMP_LOCATION)
VALUES
(:APP_NAME, :TEST_RUN_NO, :TEST_TYPE, :RELEASE_NAME, :TEST_DATE, :TEST_STATUS, :LOAD_PERCENTAGE, :INSTALLERS, 
:SCENARIOS_COUNT, :EXPECTED_WPM, :ACTIVE_USERS, :CONCURRENT_USERS, :APP_CORE_ALLOCATED, :APP_MEM_ALLOCATED, 
:DB_CORE_ALLOCATED, :DB_MEM_ALLOCATED, :APP_CORE_UTILIZED, :APP_MEM_UTILIZED, :DB_CORE_UTILIZED, :DB_MEM_UTILIZED, 
:ACHIEVED_WPM, :TOTAL_TRANSACTIONS, :TOTAL_FAILED_TRANSACTIONS, :TEST_DURATION, :THROUGHPUT, :HITS_PER_SEC, 
:THREAD_COUNT, :LOGICAL_IO_BLOCK_CHANGES, :TEST_SCOPE, :CHANGES_MADE, :REMARKS, :AVG_PAGE_PER_SEC, :AVG_REQ_RESP_TIME,
:RAMP_UP_TIME, :SVN_PATH, :RAMP_UP_POLICY, execution_summary_seq.NEXTVAL, :HEAP_DUMP_LOCATION, :THREAD_DUMP_LOCATION)
'''

format_sql = {
    'APP_NAME': APP_NAME,
    'TEST_RUN_NO': TEST_RUN_NO,
    'TEST_TYPE': TEST_TYPE,
    'RELEASE_NAME': RELEASE_NAME,
    'TEST_DATE': TEST_DATE,
    'TEST_STATUS': TEST_STATUS,
    'LOAD_PERCENTAGE': LOAD_PERCENTAGE,
    'INSTALLERS': INSTALLERS,
    'SCENARIOS_COUNT': SCENARIOS_COUNT,
    'EXPECTED_WPM': EXPECTED_WPM,
    'CONCURRENT_USERS': CONCURRENT_USERS,
    'APP_CORE_ALLOCATED': APP_CORE_ALLOCATED,
    'APP_MEM_ALLOCATED': APP_MEM_ALLOCATED,
    'DB_CORE_ALLOCATED': DB_CORE_ALLOCATED,
    'DB_MEM_ALLOCATED': DB_MEM_ALLOCATED,
    'APP_CORE_UTILIZED': APP_CORE_UTILIZED,
    'APP_MEM_UTILIZED': APP_MEM_UTILIZED,
    'DB_CORE_UTILIZED': DB_CORE_UTILIZED,
    'DB_MEM_UTILIZED': DB_MEM_UTILIZED,
    'ACHIEVED_WPM': ACHIEVED_WPM,
    'TOTAL_TRANSACTIONS': TOTAL_TRANSACTIONS,
    'TOTAL_FAILED_TRANSACTIONS': TOTAL_FAILED_TRANSACTIONS,
    'TEST_DURATION': TEST_DURATION,
    'THROUGHPUT': THROUGHPUT,
    'HITS_PER_SEC': HITS_PER_SEC,
    'THREAD_COUNT': THREAD_COUNT,
    'LOGICAL_IO_BLOCK_CHANGES': LOGICAL_IO_BLOCK_CHANGES,
    'TEST_SCOPE': TEST_SCOPE,
    'CHANGES_MADE': CHANGES_MADE,
    'REMARKS': REMARKS,
    'AVG_PAGE_PER_SEC': AVG_PAGE_PER_SEC,
    'AVG_REQ_RESP_TIME': AVG_REQ_RESP_TIME,
    'RAMP_UP_TIME': RAMP_UP_TIME,
    'SVN_PATH': SVN_PATH,
    'RAMP_UP_POLICY': RAMP_UP_POLICY,
    'HEAP_DUMP_LOCATION': HEAP_DUMP_LOCATION,
    'THREAD_DUMP_LOCATION': THREAD_DUMP_LOCATION
}

gps.global_cursor.execute(sql, format_sql)