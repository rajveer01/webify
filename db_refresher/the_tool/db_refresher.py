import PySimpleGUI as sg
import logging
import os
import time
import json
from datetime import datetime as dt
import paramiko
import cx_Oracle
from paramiko import SSHClient
import smtplib
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.headerregistry import Address
import sys
from math import floor


exp = 'Exception: '


class IncrementNum:
    x = 0
    @property
    def f_num(self):
        self.x = floor(self.x) + 1
        return str(self.x) + ": "

    @property
    def s_num(self):
        if self.x % 1 > 0.7:
            self.x -= 0.7
        else:
            self.x += 0.1
        return str(round(self.x, 1)) + ': '


def execute_ssh_assync(command):
    logging.info(f'Got This Command {command}')
    _, out, _ = ssh.exec_command(command)
    logging.info(out.read().decode())
    out.channel.recv_exit_status()
    logging.info('Command Completed')
    return True


n = IncrementNum()

args = sys.argv

'''
['python', 
0=> f'{tool_dir}/db_refresher.py', 
1=> f'param_files/{file_name}',  # param_files/New Schema Name_db_ip_Jan 20, 2020 10.06.59 PM _.json
2=> f'{file_name}.log',   # New Schema Name_db_ip_Jan 20, 2020 10.06.59 PM _.json.log
3=> 'Run Logs',
4=> f'{tool_dir}',  # tool Location
5=> 'import',

],
'''


if len(args) < 6:
    print(f'{exp} Not Called with Proper parameters {args}')
    raise Exception(f'Not Called with Proper parameters {args}')


parameter_file = str(args[1]).strip()
log_file = str(args[2]).strip()
log_location = str(args[3]).strip()
tool_location = str(args[4]).strip()
operation = str(args[5]).strip()

os.chdir(tool_location)

logging.basicConfig(
    filename=os.path.join(log_location, log_file),
    level=logging.INFO,
    format='''
%(levelname)s - %(asctime)s
    File: %(filename)s 
    Line: %(lineno)d
    Func: %(funcName)s
    MSG: %(message)s
''')

logging.info(f'Got Sys arguments as {args}')

with open(parameter_file) as f:
    input_values = json.loads(f.read())

logging.info(input_values)


TimeStamp = dt.now().strftime('%b %d, %Y %I.%M.%S %p ')


'''Assigning dict Values To variables'''
# From Ui, User inputs

sid = input_values['sid']
db_port = input_values['db_port']
user = input_values['user']  # DB_SSH_User
pwd = input_values['pwd']  # DB_SSH_Password
db_ssh_Port = input_values['db_ssh_Port']  # DB_SSH_Password
SystemUserPassword = input_values['SystemUserPassword']
No_Of_DataFiles = input_values['No_Of_DataFiles']
No_Of_IndexFiles = input_values['No_Of_IndexFiles']
enterprise_name = input_values['enterprise_name']
result_database_name = input_values['result_database_name']
db_host = input_values['db_hostname']
curr_schema_name = input_values['current_schema_name']
dump_file_directory = input_values['dump_file_directory']

print(n.f_num, 'Got the Parameters')
ssh = SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(db_host, port=db_ssh_Port, username=user, password=pwd, auth_timeout=5000)

print(n.f_num, 'Connected to DB via SSH')

if operation == 'import':
    export_or_import = 'import'
    new_schema_name = input_values['new_schema_name']
    new_schema_name = curr_schema_name if new_schema_name == "" else new_schema_name
    table_space_location = input_values['table_space_location']
    dump_file_name = input_values['dump_file_name']
    dump_schema_name = input_values['dump_schema_name']
    REMAP_TABLESPACE_DATA=input_values['REMAP_TABLESPACE_DATA']
    REMAP_TABLESPACE_IDX=input_values['REMAP_TABLESPACE_IDX']
    db_log_file_location = '/Data/oracle/app/oracle/admin/db11/dpdump'

    '''Dropping Schema and TablesSpace'''

    command_for_drop_schema_ts = '''
    sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
    shutdown immediate;
    startup restrict;
    DROP USER {curr_schema_name} CASCADE;
    shutdown immediate;
    startup;
    DROP TABLESPACE {curr_schema_name}_DATA INCLUDING CONTENTS AND DATAFILES;
    DROP TABLESPACE {curr_schema_name}_IDX INCLUDING CONTENTS and DATAFILES;
    !
    '''.format(SystemUserPassword=SystemUserPassword, curr_schema_name=curr_schema_name)

    execute_ssh_assync(command_for_drop_schema_ts)

    '''Create TS and Schema'''

    command_for_TS = '''
    sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
    CREATE TABLESPACE {new_schema_name}_DATA DATAFILE '{table_space_location}/{new_schema_name}_DATA.DBF' SIZE 512M AUTOEXTEND ON NEXT 512M MAXSIZE UNLIMITED LOGGING ONLINE PERMANENT EXTENT MANAGEMENT LOCAL AUTOALLOCATE BLOCKSIZE 8K SEGMENT SPACE MANAGEMENT AUTO FLASHBACK ON;
    !
    '''.format(SystemUserPassword=SystemUserPassword,
               new_schema_name=new_schema_name,
               table_space_location=table_space_location)

    execute_ssh_assync(command_for_TS)

    for i in range(1, int(No_Of_DataFiles)):
        command_for_df = '''
        sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
        ALTER TABLESPACE {new_schema_name}_DATA ADD DATAFILE '{table_space_location}/{new_schema_name}_DATA{i}.DBF' size 512m AUTOEXTEND ON NEXT 512m MAXSIZE unlimited;
        !
        '''.format(SystemUserPassword=SystemUserPassword,
                   new_schema_name=new_schema_name,
                   table_space_location=table_space_location,
                   i=i)
        execute_ssh_assync(command_for_df)

    '''Creating Index Files'''

    command_for_idx = '''
    sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
    CREATE TABLESPACE {new_schema_name}_IDX DATAFILE '{table_space_location}/{new_schema_name}_IDX.DBF' SIZE 512M AUTOEXTEND ON NEXT 512M MAXSIZE UNLIMITED LOGGING ONLINE PERMANENT EXTENT MANAGEMENT LOCAL AUTOALLOCATE BLOCKSIZE 8K SEGMENT SPACE MANAGEMENT AUTO FLASHBACK ON;
    !
    '''.format(SystemUserPassword=SystemUserPassword,
               new_schema_name=new_schema_name,
               table_space_location=table_space_location)

    execute_ssh_assync(command_for_idx)

    for i in range(1, int(No_Of_IndexFiles)):
        command_for_idx = '''
        sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
        ALTER TABLESPACE {new_schema_name}_IDX ADD DATAFILE '{table_space_location}/{new_schema_name}_IDX{i}.DBF' size 512m AUTOEXTEND ON NEXT 512m MAXSIZE unlimited;
        !
        '''.format(SystemUserPassword=SystemUserPassword,
                   new_schema_name=new_schema_name,
                   table_space_location=table_space_location,
                   i=i)
        execute_ssh_assync(command_for_idx)

    '''Creating User'''

    command_for_user = '''
    sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
    CREATE USER {new_schema_name} IDENTIFIED BY {new_schema_name} DEFAULT TABLESPACE {new_schema_name}_DATA TEMPORARY TABLESPACE TEMP PROFILE DEFAULT ACCOUNT UNLOCK;
    commit;
    !
    '''.format(SystemUserPassword=SystemUserPassword,
               new_schema_name=new_schema_name)

    execute_ssh_assync(command_for_user)

    '''Granting Permission'''

    command_for_permission = '''
    sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
    GRANT DBA TO {new_schema_name};
    ALTER USER {new_schema_name} DEFAULT ROLE ALL;
    GRANT CREATE SEQUENCE TO {new_schema_name};
    GRANT CREATE VIEW TO {new_schema_name};
    GRANT UNLIMITED TABLESPACE TO {new_schema_name};
    GRANT CREATE SESSION TO {new_schema_name};
    GRANT CREATE PROCEDURE TO {new_schema_name};
    GRANT SELECT ANY DICTIONARY TO {new_schema_name};
    GRANT CREATE ANY TYPE TO {new_schema_name};
    GRANT CREATE ANY TRIGGER TO {new_schema_name};
    GRANT CREATE ANY INDEX TO {new_schema_name};
    GRANT CREATE TABLE TO {new_schema_name};
    GRANT ALTER SESSION TO {new_schema_name};
    ALTER USER {new_schema_name} QUOTA UNLIMITED ON {new_schema_name}_IDX;
    ALTER USER {new_schema_name} QUOTA UNLIMITED ON {new_schema_name}_DATA;
    GRANT CREATE TYPE to {new_schema_name};
    GRANT CREATE TRIGGER to {new_schema_name};
    grant all on directory {dump_file_directory} to {new_schema_name};
    GRANT CREATE ANY CONTEXT TO {new_schema_name};
    !
    '''.format(SystemUserPassword=SystemUserPassword,
               new_schema_name=new_schema_name,
               dump_file_directory=dump_file_directory)

    execute_ssh_assync(command_for_permission)

    '''Importing DB'''
    print(TimeStamp)
    command_for_import_db = '''impdp {new_schema_name}/{new_schema_name} DIRECTORY={dump_file_directory} DUMPFILE={dump_file_name} LOGFILE={new_schema_name}{TimeStamp}Import.log FULL=Y REMAP_SCHEMA={dump_schema_name}:{new_schema_name} REMAP_TABLESPACE={REMAP_TABLESPACE_DATA}:{new_schema_name}_DATA, REMAP_TABLESPACE={REMAP_TABLESPACE_IDX}:{new_schema_name}_IDX TRANSFORM=OID:N
    '''.format(new_schema_name=new_schema_name, dump_file_directory=dump_file_directory,
               dump_file_name=dump_file_name, dump_schema_name=dump_schema_name, TimeStamp=TimeStamp,
               REMAP_TABLESPACE_DATA=REMAP_TABLESPACE_DATA, REMAP_TABLESPACE_IDX=REMAP_TABLESPACE_IDX)

    execute_ssh_assync(command_for_import_db)
    print(TimeStamp)

    with cx_Oracle.connect(
            '{new_schema_name}/{new_schema_name}@{db_host}:{db_port}/{sid}'.format(new_schema_name=new_schema_name,
                                                                                   db_host=db_host,
                                                                                   db_port=db_port,
                                                                                   sid=sid)) as conn:
        with conn.cursor() as cursor:
            cursor.execute('select DIRECTORY_PATH from DBA_DIRECTORIES where DIRECTORY_NAME = :DIRECTORY_NAME',
                           {'DIRECTORY_NAME': dump_file_directory})
            db_log_file_location = cursor.fetchone()[0]
            print(db_log_file_location)
    content = ''

    with ssh.open_sftp() as sftp:
        to_find = 'Job "{new_schema_name}"."SYS_IMPORT_FULL_01" completed'.format(
            new_schema_name=new_schema_name.upper())
        # Job "TPM70SP5PLAB"."SYS_IMPORT_FULL_01" completed with 79 error(s) at Thu Nov 7 13:23:16 2019 elapsed 0 03:26:07
        is_to_find_Not_available = True
        while is_to_find_Not_available:
            remote_file_to_open = '{db_log_file_location}/{new_schema_name}{TimeStamp}Import.log'.format(
                new_schema_name=new_schema_name, TimeStamp=TimeStamp, db_log_file_location=db_log_file_location)
            logging.info('Got remote File for logs As {}'.format(remote_file_to_open))
            with sftp.open(remote_file_to_open) as remote_file:
                content = remote_file.read().decode()
                remote_file.seek(0)
                import_logs = remote_file.readlines()
                logging.info(import_logs[-5:])
                if to_find in content:
                    is_to_find_Not_available = False
                logging.info('waiting For 3 minutes And Sleeping')
                time.sleep(30)

    '''Update Table '''

    with cx_Oracle.connect(
            '{new_schema_name}/{new_schema_name}@{db_host}:{db_port}/{sid}'.format(new_schema_name=new_schema_name,
                                                                                   db_host=db_host,
                                                                                   db_port=db_port,
                                                                                   sid=sid)) as conn:
        with conn.cursor() as cursor:
            query = "Update si_ent set enterprise_name = :enterprise_name"
            cursor.execute(query, {'enterprise_name': enterprise_name})
            logging.info('query executed : {}'.format(query))

            query = "update si_ent_applications set db_login = :SchemaName, db_password = :SchemaName where application_id = 100000"
            cursor.execute(query, {'SchemaName': new_schema_name})
            logging.info('query executed : {}'.format(query))

            query = "Update MS_APPS_MDF_FLOW_XML set enterprise = :enterprise_name"
            cursor.execute(query, {'enterprise_name': enterprise_name})
            logging.info('query executed : {}'.format(query))

            query = "update si_metrics_t set result_database_name = :result_database_name"
            cursor.execute(query, {'result_database_name': result_database_name})
            logging.info('query executed : {}'.format(query))

            '''Compile invalid objects'''

            invalid_Obj_Query = '''
            BEGIN
           COMPILE_ALL_INVALID_OBJECTS;
    EXCEPTION
    WHEN OTHERS THEN
           DBMS_OUTPUT.PUT_LINE('Please compile all the objects in the schema');
    END;
            '''
            cursor.execute(invalid_Obj_Query)
            logging.info('query executed : {}'.format(invalid_Obj_Query))

            invalid_Obj_Query = '''select 'ALTER ' || OBJECT_TYPE ||' "' ||dbms_java.longname(object_name) ||'" RESOLVER ((* {new_schema_name})(* PUBLIC)) RESOLVE ' from all_objects where owner= '{new_schema_name}'  AND STATUS='INVALID' and object_type ='JAVA CLASS' '''.format(
                new_schema_name=new_schema_name)

            cursor.execute(invalid_Obj_Query)
            logging.info('query executed : {}'.format(invalid_Obj_Query))

            alter_Results = cursor.fetchall()
            print(alter_Results)
            logging.info('got alter results as : {}'.format(alter_Results))

            for i in alter_Results:
                print('One Alter Command', str(i[0]))
                cursor.execute(str(i[0]))
                logging.info('query executed : {}'.format(i))

            cursor.execute(invalid_Obj_Query)
            res = cursor.fetchall()
            if res is None:
                logging.info('Invalid Objects Found here \n {}'.format(res))

    '''Gather Stats'''

    command_for_gather = '''
    sqlplus sys/{SystemUserPassword} 'as sysdba'<<!
    execute dbms_stats.gather_schema_stats(ownname => '{new_schema_name}', cascade => true);
    !
    '''.format(SystemUserPassword=SystemUserPassword,
               new_schema_name=new_schema_name)

    execute_ssh_assync(command_for_gather)

    '''Send Mail'''

    msg = EmailMessage()
    with open("refresher_tool_logs/db_Import_Export{}.log".format(TimeStamp), 'rb') as f:
        f_data = f.read()
        f_name = f.name

    EMAIL_ADDRESS = "rndplab@gmail.com"
    EMAIL_PASSWORD = "performance@2019"

    msg["Subject"] = "Import Done For - {new_schema_name} at {TimeStamp}".format(TimeStamp=TimeStamp,
                                                                                 new_schema_name=new_schema_name)
    msg['From'] = Address(display_name='R&DPLab Metricstream.com', addr_spec='rajveer.singh@metricstream.com')
    msg['To'] = input_values['emails']
    msg.set_content('Image Attached...')
    att = MIMEApplication(f_data)
    att.add_header('Content-Disposition', 'attachment', filename=f_name)
    msg.make_alternative()
    msg.attach(att)
    html_page = '''
        <p>Hi,</p>
        <p>Following Queries/Commands have been Executed </p>
        <ul>
        <li>Dropping the Current Schema {curr_schema_name}</li>
        <li>Delete the TS and Datafiles for the Current Schema {curr_schema_name}</li>
        <li>Deleted Index files for the current Schema {curr_schema_name}</li>
        <li>Creates New Schema {new_schema_name}</li>
        <li>Granted Permissions to {new_schema_name}</li>
        <li>Import from the file {dump_file_name}</li>
        <li>Compiling Invalid Object</li>
        <li>Update Table</li>
        <li>Gather Stats</li>
        </ul>
        <p></p>
        <p>Thanks,</p>
        <p>RnD PLAB Team</p>
        '''.format(curr_schema_name=curr_schema_name, new_schema_name=new_schema_name,
                   dump_file_name=dump_file_name)
    msg.add_alternative(html_page, subtype="html")

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Please ask to check")


else:
    export_or_import = 'export'

    command_for_export_db = f'''expdp {curr_schema_name}/{curr_schema_name} DIRECTORY={dump_file_directory}  DUMPFILE={curr_schema_name}{TimeStamp}.dmp LOGFILE={curr_schema_name}{TimeStamp}Export.log SCHEMAS={curr_schema_name} EXCLUDE=STATISTICS'''

    execute_ssh_assync(command_for_export_db)
    '''Send Mail'''
    msg = EmailMessage()
    with open("refresher_tool_logs/db_Import_Export{}.log".format(TimeStamp), 'rb') as f:
        f_data = f.read()
        f_name = f.name

    EMAIL_ADDRESS = "rndplab@gmail.com"
    EMAIL_PASSWORD = "performance@2019"

    msg["Subject"] = f"Export Done For - {curr_schema_name} at {TimeStamp}"
    msg['From'] = Address(display_name='R&DPLab Metricstream.com', addr_spec='rajveer.singh@metricstream.com')
    msg['To'] = input_values['emails']
    logging.info(input_values['emails'])
    msg.set_content('Image Attached...')
    att = MIMEApplication(f_data)
    att.add_header('Content-Disposition', 'attachment', filename=f_name)
    msg.make_alternative()
    msg.attach(att)
    html_page = '''
        <p>Hi,</p>
        <p>Import Has Been Successful. Please proceed with Sanity.&#128540;</p>
        <p></p>
        <p>Thanks,</p>
        <p>RnD PLAB Team</p>
        '''
    msg.add_alternative(html_page, subtype="html")

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print("Please ask to check")




