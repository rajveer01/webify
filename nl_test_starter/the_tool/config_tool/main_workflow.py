import paramiko
import os
import all_loggers
import pandas as pd
from config_tool import xml_handler
from config_tool import db_handler
from config_tool import non_xml_handler
from config_tool import https
import datetime
from datetime import datetime
import requests
import json

logging = all_loggers.logger_log


# log_format = '''
# %(levelname)s - %(asctime)s
#     File: %(filename)s
#     Line: %(lineno)d
#     Func: %(funcName)s
#     MSG: %(message)s
# '''
#
# logging.basicConfig(filename='config_checker.log', level=logging.INFO, format=log_format)


def run_config_tool(tool_params):
    # class AppParams:
    #     APP: str
    #     APP_IP: str
    #     DB_IP: str
    #     SYSTEMI_PATH: str
    #     DB_HOME: str
    #     SCHEMA_NAME: str
    #     SCHEMA_PWD: str
    #     APP_ORACLE_PWD: str
    #     APP_ROOT_PWD: str
    #     DB_ORACLE_PWD: str
    #     DB_ROOT_PWD: str
    #     THREADDUMP_FILE_PATH: str
    #     WINDOWS_IP: str
    #     ACTIVATION_FOR_THIS_RELEASE: str
    #     JDK_PATH: str
    #     APP_FULL_NAME: str
    #     WINDOWS_USER_NAME: str
    #     WINDOWS_USER_PWD: str
    #     NL_BIN_DIR: str
    #     NL_LICENSE_ID: str
    #     EXECUTION_IP: str
    #     EXECUTION_PROJECT_FOLDER: str
    #     EXECUTION_SCENARIO: str
    #     MONITOR_IP: str
    #     MONITOR_PROJECT_LOCATION: str
    #     MONITOR_SCENARIO: str
    #     TEST_RUN_NO: int
    #     TEST_DESCRIPTION: str
    #     RELEASE_NAME: str
    #     ARTIFACTS_FOLDER: str
    #     SVN_ARTIFACT_FOLDER: str
    #     SVN_OP_LOCATION: str
    #     SVN_USER_NAME: str
    #     SVN_PASSWORD: str
    #     TOTAL_USERS: int
    #     CHANGE_HISTORY: str
    #     ORACLE_DB_PORT: int
    #     ORACLE_DB_ID: str
    #     COMPARE_WITH_OLD: int
    #     WPM_MATTERS: int
    #     TEST_TYPE: str
    #     THREAD_DUMP_LOCATION: str
    #     HEAP_DUMP_LOCATION: str
    #     OLD_RUN: int
    #     OLD_TEST_TYPE: str
    #     OLD_RELEASE_NAME: str
    #     TEST_SCOPE: str
    #     CHANGES_MADE: str
    #     TO_MAIL_FILE: str
    #     INSTALLERS_TO_AVOID: str
    #     NL_LICENSE_LEASE_H: int
    #     NTS: str
    #     NTS_LOGIN: str
    #     NL_LICENSE_ID: str
    #
    #     def __init__(self, APP: str):
    #         pass
    #
    # tool_params = AppParams(**{})

    def get_linux_infrastructure_by_hostname(hostname, port, username, password):
        json_data = json.dumps({
            "hostname": hostname,
            "port": port,
            "username": username,
            "password": password
        })
        headers = {"Content-type": "application/json"}
        with requests.post(f'{tool_params.BASE_URL}/apis/linux_infrastructure/', data=json_data,
                           headers=headers) as resp:
            return resp.json()

    db_linux_infrastructure_details = get_linux_infrastructure_by_hostname(hostname=tool_params.DB_IP,
                                                                           port=22,
                                                                           username='oracle',
                                                                           password=tool_params.DB_ORACLE_PWD)

    app_linux_infrastructure_details = get_linux_infrastructure_by_hostname(hostname=tool_params.APP_IP,
                                                                            port=22,
                                                                            username='oracle',
                                                                            password=tool_params.APP_ORACLE_PWD)
    app_name = tool_params.APP
    db_ip = tool_params.DB_IP
    username_db = 'oracle'
    pwd_db = tool_params.DB_ORACLE_PWD
    root_passwd = tool_params.DB_ROOT_PWD
    db_home = tool_params.DB_HOME
    schema = tool_params.SCHEMA_NAME
    schema_psw = tool_params.SCHEMA_PWD
    db_port = tool_params.ORACLE_DB_PORT
    sid = tool_params.ORACLE_DB_ID
    db_core = db_linux_infrastructure_details['cores']
    db_ram = db_linux_infrastructure_details['ram']
    app_ip = tool_params.APP_IP
    SYSTEMi = tool_params.SYSTEMI_PATH
    username_app = 'oracle'
    pwd_ap = tool_params.APP_ORACLE_PWD
    app_core = app_linux_infrastructure_details['cores']
    app_ram = app_linux_infrastructure_details['ram']

    now = datetime.now()
    current_time = now.strftime("%d_%m_%Y_%H_%M_%S")

    out_put_loc = os.getcwd()
    my_rel_path = os.path.dirname(os.path.relpath(__file__))
    in_put_loc = os.path.join(my_rel_path, 'Requirement.xlsx')

    ssh_app = paramiko.SSHClient()
    ssh_app.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh_app.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))

    ssh_app.connect(app_ip, username=username_app, password=pwd_ap)
    sftp_app = ssh_app.open_sftp()

    logging.info(f"Successfully made the ssh connection with APP server : {app_ip}")

    ssh_db = paramiko.SSHClient()
    ssh_db.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh_db.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh_db.connect(db_ip, username=username_db, password=pwd_db)
    sftp_db = ssh_db.open_sftp()

    logging.info(f"Successfully made the ssh connection with DB server : {db_ip}")

    ssh_db_root = paramiko.SSHClient()
    ssh_db_root.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh_db_root.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh_db_root.connect(db_ip, username='root', password=root_passwd)

    logging.info(f"Successfully made the ssh connection with DB server as root : {db_ip}")

    xlread = pd.read_excel(in_put_loc)
    error = []
    information = {  # pandas dataset variable
        'Area': [],
        'File Name': [],
        'File_Loction': [],
        'Action Type': [],
        'Purpose': [],
        'Previous': [],
        'Expected': [],
        'Content Location': [],
        'Status': [],
        'Last Stats Run Date': [],
        'SSL Config Status': [],
        'Last Index Rebuild Run Date':[]
    }

    for i in range(len(xlread)):
        information['Area'].append(xlread.iloc[i]['Area'])
        information['File Name'].append(xlread.iloc[i]['File Name'])
        information['File_Loction'].append(xlread.iloc[i]['File Location'])  # pandas data append
        information['Purpose'].append(xlread.iloc[i]['Purpose'])
        information['Content Location'].append(xlread.iloc[i]['Content Location'])
        information['Action Type'].append(xlread.iloc[i]['Action Type'])

        if (xlread.iloc[i]['File Name'][-4:]) == '.xml' and xlread.iloc[i]['File Name'] != 'config.client.xml':
            # try:
            file = xlread.iloc[i]['File Location'].format(SYSTEMi=SYSTEMi) + '/' + xlread.iloc[i]['File Name']
            connection_obj = sftp_app if xlread.iloc[i]['Area'].lower() == 'app' else sftp_db
            print(file)

            file_data = connection_obj.open(file).read()
            xpath = xlread.iloc[i]['Content Location']
            data = xlread.iloc[i]['Expected']
            information['Last Stats Run Date'].append('')
            information['Last Index Rebuild Run Date'].append('')

            try:
                previous_val, root, new_val = xml_handler.xml_handler(file_data.decode(), xpath,
                                                                      data)  # to handle xml files
                print(previous_val)
                information['Expected'].append(new_val)
                information['Previous'].append(previous_val)
                with sftp_app.open(file, 'w') as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + root)
                    print('done')
                information['Status'].append('Success!')
                logging.info("Successfully Handled xml related files from the servers")
            except:
                error.append(xpath)
                print(error)
                information['Expected'].append('-')
                information['Previous'].append('-')
                information['Status'].append('Fail!')

        elif (xlread.iloc[i]['File Name'][-4:]) == '.ora':  # Handling db related function
            file = xlread.iloc[i]['File Location'].format(db_home=db_home) + '/' + xlread.iloc[i]['File Name']
            connection_obj = sftp_app if xlread.iloc[i]['Area'].lower() == 'app' else sftp_db
            print('handling db')

            previous_val, exp_mem, x, y = db_handler.db_handler(file, ssh_db, ssh_db_root, connection_obj, db_ram, schema,
                                                             schema_psw, db_port, sid, db_ip)
            information['Expected'].append(exp_mem)
            print(previous_val)
            information['Last Stats Run Date'].append(x)
            information['Last Index Rebuild Run Date'].append(y)

            information['Previous'].append(previous_val)
            information['Status'].append('Success!')
            logging.info("Successfully Handled .ora file from DB Server :{}".format(db_ip))

        else:
            file = xlread.iloc[i]['File Location'].format(SYSTEMi=SYSTEMi) + '/' + xlread.iloc[i][
                'File Name']  # function calling for non xml handing
            delimiter = xlread.iloc[i]['Content Location']
            value = xlread.iloc[i]['Expected']
            previous_val, expected_value = non_xml_handler.non_xml_handler(file, sftp_app, delimiter, value, app_ram)

            information['Last Stats Run Date'].append('')
            information['Last Index Rebuild Run Date'].append('')
            information['Expected'].append(expected_value)
            information['Previous'].append(previous_val)
            information['Status'].append('Success!')
            logging.info(
                "Successfully Handled non xml files (tomcat.sh,httpd.config) files from APP Server :{}".format(app_ip))

    http = https.ssl(app_ip, username_app, pwd_ap, SYSTEMi, schema_psw)
    print(http)
    information['SSL Config Status'].append(http)
    for i in range(1, len(information['Status'])):
        information['SSL Config Status'].append('')

    df = pd.DataFrame(information)

    print(information)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    output_file_path = os.path.join(out_put_loc, 'Artifacts', f'{app_name}_Result_Status_{current_time}.xlsx')
    writer = pd.ExcelWriter(output_file_path, engine='xlsxwriter')

    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='RESULT')

    workbook = writer.book
    worksheet = writer.sheets['RESULT']
    red_format = workbook.add_format({'bg_color': 'red'})
    green_format = workbook.add_format({'bg_color': 'green'})

    worksheet.conditional_format('J2:J13', {'type': 'text',
                                            'criteria': 'containsText',
                                            'value': 'Fail!',
                                            'format': red_format})

    worksheet.conditional_format('J2:J14', {'type': 'text',
                                            'criteria': 'containsText',
                                            'value': 'Success!',
                                            'format': green_format})

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    if 'CONFIG_TOOL_ARTIFACTS' not in sftp_app.listdir(SYSTEMi):
        sftp_app.mkdir(f'{SYSTEMi}/CONFIG_TOOL_ARTIFACTS')

    config_tool_artifacts_dir = f'{SYSTEMi}/CONFIG_TOOL_ARTIFACTS/'
    for one_file in sftp_app.listdir(config_tool_artifacts_dir):
        if 'OLD - ' not in one_file:
            sftp_app.rename(f'{config_tool_artifacts_dir}/{one_file}', f'{config_tool_artifacts_dir}/OLD - {one_file}')

    sftp_app.put(output_file_path, f'{config_tool_artifacts_dir}/{os.path.basename(output_file_path)}')

    sftp_app.close()
    ssh_app.close()

    sftp_db.close()
    ssh_db.close()

    return all([False if i == 'Fail!' else True for i in information['Status']])

