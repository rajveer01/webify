import json
import tempfile
import time
import xml.etree.ElementTree as Et
import zipfile
from datetime import datetime as dt
from urllib.parse import unquote
import re
import requests as req
import glob
import os
import sys
import shutil

import requests
from svn.remote import RemoteClient as Rc

import awr_and_addm
import copy_logs
import format_table_from_latest_results
import gps
import index_file_in_latest_folder
import installer_versions_table
import neoload_reports
import nl_results_to_db_table_v2
import pb
import prerequisite
import remote_drive_mounter
import server_utilization
import upload_to_svn
import utilisation_table
import zip_folders
import all_loggers

all_loggers.logger_log.info('testing logger log')
all_loggers.logger_log.exception('testing logger exception')

'''
Call this file form Command Line With Following Arguments
"IAD" "Feb 2020 Release-IAD-Load Run-9.log" "Artifacts/Feb 2020 Release/IAD/Run Logs"
APP     Log File Name                       "Log Directory"
'''

try:

    """Mounting the Remote Directories"""

    print(pb.n.f_num, 'Mounting Remote Dirs for Neoload, Creating CMD Service')
    remote_drive_mounter.mount(gps.execution_project_folder)

    # if gps.monitor_available and False:
    #     remote_drive_mounter.mount(gps.monitor_project_location)

    print(pb.n.f_num, 'Running Prerequisite')

    '''Run Prerequisite.py file to test few things.'''

    # todo refactor prerequisite code.
    # todo Mount Only If Not Mounted Already

    prerequisite.validate()

    # Keep Checking till the test stops

    url_g = f"http://{gps.execution_IP}:7400/Runtime/v1/Service.svc/GetStatus"
    data = {"d": {}}
    data = json.dumps(data)
    headers = {"Content-type": "application/json"}

    print(pb.n.f_num, f'checking the project to stop...@{gps.execution_IP}')
    all_loggers.logger_log.info(
        "Keep Checking till the test stops in, {}".format(url_g))

    resp = requests.post(url_g, data=data, headers=headers)

    # Waiting for Neoload to stop the test

    while json.loads(resp.text)["d"]["Status"] != "READY":
        time.sleep(30)
        print('\b' * 1000, pb.n.s_num, "Waiting for NL test to stop- " +
              json.loads(resp.text)["d"]["Status"], end='')
        all_loggers.logger_log.info(
            "\tWaiting for NL test to stop- " + json.loads(resp.text)["d"]["Status"])
        resp = requests.post(url_g, data=data, headers=headers)
    resp.close()
    print(pb.n.f_num, 'Test Stopped')
    all_loggers.logger_log.info('Test Stopped')

    # Stopping the Monitor Project in {} from Running

    if gps.monitor_available:
        pass
        # print(pb.n.f_num, f'stopping Monitor Project@{gps.monitor_IP}...')
        # all_loggers.logger_log.info(
        #     f"Stopping the Monitor Project in {gps.monitor_IP} from Running")
        #
        # stop_end_point = "http://%s:7400/Runtime/v1/Service.svc/StopTest" % gps.monitor_IP
        # data = {"d": {"ForceStop": True}}
        # data = json.dumps(data)
        # headers = {"Content-type": "application/json"}
        # resp = requests.post(stop_end_point, data=data, headers=headers)
        # all_loggers.logger_log.info(
        #     f"Status for monitor project stopping at {stop_end_point} - {resp.status_code}\n" + resp.text)
        # resp.close()

    # get the index file from the latest Folder of the results in

    all_loggers.logger_log.info(f"Getting the latest folder in {os.path.join(gps.execution_project_folder, 'results')}")
    print(pb.n.f_num, f'Getting the latest folder... @{os.path.join(gps.execution_project_folder, "results")}')

    gps.latest_folder, gps.index_from_res_path = index_file_in_latest_folder.get_index_file(
        os.path.join(gps.execution_project_folder,
                     "results"))

    all_loggers.logger_log.info(f'''Got the index.html in Latest Folder {
    os.path.join(gps.execution_project_folder, 'results')} of the results as {gps.index_from_res_path}''')

    # Create the Artifact folder

    all_loggers.logger_log.info("Create the Artifact folder")
    dt_string = dt.now().strftime("_%d_%m_%Y_%H_%M_%S")
    # Artifact_F_name = (
    #     gps.app_name + "_" + gps.run_description + "_Run_" + gps.run + dt_string
    # )

    # gps.artifacts_folder = os.path.join(gps.artifacts_folder, Artifact_F_name)
    if not os.path.exists(gps.artifacts_folder):
        os.makedirs(gps.artifacts_folder)

    all_loggers.logger_log.info(
        "Created the Artifact folder {}".format(gps.artifacts_folder))

    # Create awr and Addmrpt and Copy to Artifact Folder

    all_loggers.logger_log.info(
        "Create awr and Addmrpt and Copy to Artifact Folder {}".format(
            gps.artifacts_folder)
    )

    print(pb.n.f_num, 'generating and copying awr and addm...')

    awr_and_addm_result = awr_and_addm.generate_and_copy()

    all_loggers.logger_log.info(
        "Might Be AWR & ADDM Done and Copied to Artifact Folder \n Results: \n {} \n".format(
            awr_and_addm_result
        )
    )

    all_loggers.logger_log.info(
        "Copy Logs to Artifacts folder to {}".format(gps.artifacts_folder))

    # Copy Logs to Artifacts folder to

    print(pb.n.f_num, 'copying logs...')

    copy_logs.copy()

    # Copy OP From SVN

    print(pb.n.f_num, 'copying OP...')
    op_local_file_path = os.path.join(gps.artifacts_folder, os.path.basename(unquote(gps.svn_op_location)))

    all_loggers.logger_log.info(f"Copy OP From SVN: {gps.svn_op_location} to {op_local_file_path}")

    client = Rc(url=gps.svn_op_location, username=gps.svn_user_name, password=gps.svn_password)

    export_response = client.run_command('export', [gps.svn_op_location, op_local_file_path])

    all_loggers.logger_log.info(f'Copied OP from SVN with response {export_response}')

    # Generate and Save the Execution Report Project_IP

    p = [
        gps.app_name,
        gps.run_description,
        "Run",
        gps.run,
        "Execution_Report",
        dt_string,
        ".pdf",
    ]
    Exe_File_name = "_".join(p).replace(" ", "_")

    all_loggers.logger_log.info(
        "Generate and Save the Execution Report Project_IP {} File_name {} Artifacts_folder {}".format(
            gps.execution_IP, Exe_File_name, gps.artifacts_folder
        )
    )
    print(pb.n.f_num, 'execution report...')

    neoload_reports.gen_report(
        project_ip=gps.execution_IP,
        file_name=Exe_File_name,
        artifacts_folder=gps.artifacts_folder,
    )

    srv_util_list = 'NA'
    if gps.monitor_available:
        # Generate and Save the Monitor Report Project_IP
        '''Old Code
        p = [
            gps.app_name,
            gps.run_description,
            "Run",
            gps.run,
            "Monitor Report",
            dt_string,
            ".pdf",
        ]
        monitor_file_name = "_".join(p).replace(" ", "_")

        all_loggers.logger_log.info(
            "Generate and Save the Monitor Report Project_IP {} File_name {} Artifacts_folder {}".format(
                gps.monitor_IP, monitor_file_name, gps.artifacts_folder
            )
        )
        print(pb.n.f_num, 'monitor report...')

        neoload_reports.gen_report(
            project_ip=gps.monitor_IP,
            file_name=monitor_file_name,
            artifacts_folder=gps.artifacts_folder,
        )

        # Get Utilisation From Monitor Project

        all_loggers.logger_log.info("Get Utilisation From Monitor Project")
        '''
        print(pb.n.f_num, 'Server utilisation...')

        srv_util_list = server_utilization.get_utilization()

    else:
        print(pb.n.f_num, 'Monitor Not Available')
        print(pb.n.f_num, 'Server Utilisation Not Available')
    # Zip the Artifacts folder

    all_loggers.logger_log.info(
        "Zip the Artifacts folder {}".format(gps.artifacts_folder))

    print(pb.n.f_num, 'Zipping the artifacts...')

    zipped_file = zip_folders.zip_it(path=gps.artifacts_folder)

    # Upload the zip {} to SVN Artifacts folder

    all_loggers.logger_log.info(
        "Upload the zip {} to SVN Artifacts folder {}".format(
            zipped_file, gps.svn_artifact_folder
        )
    )
    print(pb.n.f_num, 'Uploading to svn...')

    svn_upload_res = upload_to_svn.copy(from_file=zipped_file)

    # push the results to DB Form

    all_loggers.logger_log.info(f'''push the results to DB From {os.path.join(os.path.dirname(gps.index_from_res_path),
                                                                              r"index_files/transactions.html")}''')

    print(pb.n.f_num, 'To our db...')

    nl_results_to_db_table_v2.push_records(os.path.join(os.path.dirname(gps.index_from_res_path),
                                                        r"index_files\transactions.html"))

    all_loggers.logger_log.info("Format the mail")

    print(pb.n.f_num, 'Generating Summary table...')
    all_loggers.logger_log.info("Get Summary Table")
    txn_results_dict = format_table_from_latest_results.get_table()

    print(pb.n.f_num, 'Utilization table...')
    all_loggers.logger_log.info("Get Utilization Table")
    util_table, list_util_above_75 = utilisation_table.get_table(srv_util_list)

    print(pb.n.f_num, 'Installer versions table...')
    all_loggers.logger_log.info("Get Installer versions Table")
    installer_table = installer_versions_table.get_table()

    print(pb.n.f_num, 'Formatting Mail...')

    summary_table = txn_results_dict["table"]
    total_txns = txn_results_dict["txn_count"]

    red_txns = txn_results_dict["failed_txns"]
    yellow_txns = txn_results_dict["yellow_txns"]
    error_in_txns = txn_results_dict["error_in_txns"]
    less_wpm_scenarios = txn_results_dict["less_wpm_scenarios"]
    scn_count = txn_results_dict["scn_count"]

    nl = '\n'

    if len(list_util_above_75) > 0 or red_txns > 0 or error_in_txns != 0 or (
            less_wpm_scenarios != 0 and gps.wpm_matters):
        gps.test_status = '0'
        test_status_html = '<font color="red">Test Failed. &#10008;</font></p>'
    else:
        gps.test_status = '1'
        test_status_html = '<font color="green">Test Passed. &#10004;</font></p>'

    html_mail_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>
        <style>table {{border: 1px solid black;}}</style>
    </head>
    <body style="font-family:Calibri">
    <p>Hi Team,</p>
    <p>Please find Performance test result of {gps.app_name} for {gps.release_name}, {gps.run_description}, ran 
        on {gps.test_start_time.strftime("%b %d")}. (Run - #{gps.run})</p>

    <p><b><u>Test Scope:</u></b></p>
        <ul>
        {nl.join(map(lambda scope: f'<li> {scope.strip()} </li>', gps.test_scope)) or '<li> NA </li>'}
        </ul>
    <p><b><u>Test Status:</u></b> {test_status_html}
    <ol>
        <li>{
    f'''{red_txns} Transaction{'s' if red_txns > 1 else ''} out of {total_txns} failed to meet the expected 
                Response time SLA. <font color="red">&#10008;</font>'''
    if red_txns > 0
    else
    f'''All {total_txns} Transaction{'s have' if total_txns > 1 else ' has'} met the expected 
                    Response time SLA. <font color="green">&#10004;</font>'''
    }</li>

        <li>{
    'WPM SLA is not applicable for this run.'
    if not gps.wpm_matters
    else
    f'''{less_wpm_scenarios} Scenario{"s" if less_wpm_scenarios > 1 else ""} out of {scn_count} 
                    Failed to meet the expected WPH. <font color="red">&#10008;</font>'''
    if less_wpm_scenarios != 0
    else
    f'''All {scn_count} Scenario{"s" if scn_count > 1 else ""} have met the 
                    expected WPH. <font color="green">&#10004;</font>'''
    if less_wpm_scenarios == 0
    else ''
    }</li>

        <li>{
    'Resource utilization SLA is not applicable for this run.'
    if not gps.monitor_available
    else
    f'''{len(list_util_above_75)} Server CPU utilization performance counter failed to 
                    meet the expected SLA. <font color="red">&#10008;</font>'''
    if len(list_util_above_75) > 0
    else
    'All CPU utilization performance counter have met the expected SLA .<font color="green">&#10004;</font>'

    }</li>

        <li>{
    f'''{error_in_txns} Transaction{"s" if error_in_txns > 1 else ""} out of {total_txns} 
                have failed to meet the transaction level error SLA. <font color="red">&#10008;</font>'''
    if error_in_txns != 0
    else
    f'''All {total_txns} Transaction{"s" if total_txns > 1 else ""} have met the expected 
                    transaction level error SLA. <font color="green">&#10004;</font>'''
    }</li>
    </ol>
    {f'''
    <ul>
        <li>Also, there {'are' if yellow_txns > 1 else 'is'} {yellow_txns} 
            such transaction{'s' if yellow_txns > 1 else ''} 
            <span style='background-color: yellow;'>(highlighted in yellow)</span>, 
            whose response time{'s are' if yellow_txns > 1 else ' is'} in border 
            (within 10% of the SLA).
        </li>
    </ul>
    '''
    if yellow_txns > 0 else ''
    }

    <p><b><u>Changes Made:</u></b></p>
    <ul>
        {nl.join(map(lambda change: f'<li> {change.strip()} </li>', gps.changes_made)) or '<li> NA </li>'}    
    </ul>

    <p><a {f'href="{gps.change_history}"' if f'{gps.change_history}'.upper() not in ['NA', 'NONE']
    else ''}>{gps.change_history}</a></p>


    <p><b><u>Performance Counters:</u></b></p>
    {Et.tostring(util_table).decode()}
    <p><b><u>Summary:</u></b></p>
    {Et.tostring(summary_table).decode()}

    <p><u><b>Test Period:</b></u></p>
    <table>
        <tr style='background-color: rgb(91, 155, 213); color: white; font-weight: bold;'>
            <td>Test Period</td> <td>Date & Time</td>
        </tr>
        <tr>
            <td>Start Time</td> <td>{gps.test_start_time.strftime('%b %d, %Y %I:%M:%S %p ')} {gps.db_zone}</td>
        </tr>
        <tr>
            <td>End Time</td> <td>{gps.test_stop_time.strftime("%b %d, %Y %I:%M:%S %p ")} {gps.db_zone}</td>
        </tr>
    </table>
    <p><u><b>Test Duration:</b></u></p> {str(gps.test_stop_time - gps.test_start_time)} (hh:mm:ss)


    <p></p>
    <p><b><u>APP and DB Server Monitor:</u></b></p>
    <p>{'NA'}</p>
    <p><b><u>Java VisualVM:</u></b></p>
    <p>{'NA'}</p>
    <p><b><u>Installer Versions:</u></b></p>
    {Et.tostring(installer_table).decode()}

    <p><b><u>Result Link:</u></b> <a href="{gps.svn_artifact_folder}">{os.path.basename(gps.artifacts_folder)}</a></p>
    <p>(App Logs, Configuration Files, ADDM and AWR reports,
    Neoload Execution and Monitor Reports, Operational Profile)</p>
    <p>Thanks,</p>
    <p>PLAB TEAM</p>
    </body>
    </html>
   """

    with tempfile.NamedTemporaryFile(prefix="Mail_Content_", delete=False, suffix=".zip") as tf:
        with zipfile.ZipFile(tf.name, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
            with zipped.open('html_mail_content.txt', mode='w') as f:
                f.write(html_mail_content.encode())
        with open(tf.name, 'rb') as f:
            zip_html_mail_content = f.read()
    os.remove(tf.name)

    ''' Stat  New code for pt_results_run_result'''

    try:
        cmd = '''systeminfo | findstr /B /C:"OS Name" /C:"Total Physical Memory"'''
        raw_list = gps.rce.run_executable(
            "cmd.exe",
            arguments=f"/c {cmd}",
            timeout_seconds=15)[0].decode().splitlines()
        '''['OS Name:    Microsoft Windows Server 2012 R2 Standard', 'Total Physical Memory:     15,914 MB']'''
        nl_os_name = raw_list[0].split(':', 1)[1].strip()  # Microsoft Windows Server 2012 R2 Standard
        raw_ram = raw_list[1].split(':', 1)[1].strip()  # 15,914 MB
        nl_ram = round(float(raw_ram.rsplit(' ', 1)[0].replace(',', '_')) / 1024, 2)  # 15.54

    except Exception as e:
        all_loggers.logger_log.exception(e)
        print(e, file=sys.stderr)
        nl_os_name, nl_ram = 'NA', 'NA'
    try:
        command = "/c wmic cpu get name"
        _, nl_cpu = [i.strip()
                     for i in gps.rce.run_executable("cmd.exe", arguments=command)[0].decode().splitlines()
                     if i.strip() != ""]  # ['Name', 'Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz']
        nl_cpu_name, nl_cpu_speed = nl_cpu.rsplit('@', 1)

        command = "/c wmic cpu get NumberOfLogicalProcessors"
        _, nl_cores = [i.strip()
                       for i in gps.rce.run_executable("cmd.exe", arguments=command)[0].decode().splitlines()
                       if i.strip() != ""]  # ['NumberOfLogicalProcessors', '4']

        command = '''/c wmic NIC where "NetEnabled='true'" get "Name","Speed"'''
        _, nl_nw_raw = [i.strip()
                        for i in gps.rce.run_executable("cmd.exe", arguments=command)[0].decode().splitlines()
                        if i.strip() != ""]  # ['Name    Speed', 'Amazon Elastic Network Adapter  10000000000']
        nl_nw_speed = round(float(nl_nw_raw.rsplit(' ', 1)[-1]) / 1000_000_000, 2)

    except Exception as e:
        all_loggers.logger_log.exception(e)
        print(e, file=sys.stderr)
        nl_cpu_name, nl_cpu_speed, nl_cores, nl_nw_speed = 'NA', 'NA', 'NA', 'NA'

    all_loggers.logger_log.info(f'''Got Values From Execution Machine 
    {nl_os_name}, 
    {nl_ram}, 
    {nl_cpu_speed}, 
    {nl_cpu_name},
    {nl_cores}
    {nl_nw_speed}''')

    with gps.sftp_app.open(filename=f'{gps.SystemI_Path}/Apache/conf/httpd.conf', mode='r', ) as f:
        httpd_file = f.read().decode()
    with gps.sftp_app.open(filename=f'{gps.SystemI_Path}/Tomcat/RELEASE-NOTES', mode='r') as f:
        tomcat_release_notes = f.read().decode()
    with open(glob.glob(os.path.join(gps.execution_project_folder, '*.nlp'))[0], mode='r') as f:
        nlp_file = f.read()
    _ = os.path.join(gps.latest_folder, r'summary\index_files\images')
    with open(shutil.make_archive(_, 'zip', _), 'rb') as f:
        images_folder_zip_cont = f.read()

    db_v_cmd = r'''sqlplus / 'as sysdba'<<!
        select * from v\$version where banner like 'Ora%';
        !'''
    db_v_cmd_out = gps.ssh_db.exec_command(db_v_cmd)[1].read().decode()

    url = re.compile(r'[\n][ ]*ServerName ([a-zA-Z0-9.:-_]*)').findall(httpd_file)[0]

    try:
        apache_v = re.compile(r' Apache/([0-9.]+) ').findall(
            req.get(f'https://{url}/server-status?auto', verify=False).text)[0]
    except:
        apache_v = 'na'
    sql_pt_results_run_result = '''
    INSERT INTO PT_RESULTS_RUN_RESULT (
        APP_NAME, ROW_ID, APP_ABBR, RELEASE_NAME, USER_COUNT, 
        RAMP_TIME, EXPECTED_WPM, URL, APP_IP, DB_IP, APP_CORE, 
        APP_RAM, DB_CORE, DB_RAM, OS_APP, OS_DB, APACHE_V, 
        TOMCAT_V, DB_V, NL_MACHINE, NL_MACHINE_PROCESSOR, 
        NL_MACHINE_OS, NL_V, NL_MACHINE_CORE, NL_MACHINE_SPEED, 
        NL_MACHINE_RAM, NL_MACHINE_NW, TEST_START, TEST_END, 
        THROUGHPUT, APP_CPU, APP_MEM, DB_CPU, DB_MEM, 
        TC_THREAD_COUNT, LOGICAL_BLOCKS, ACHIEVED_WPM, 
        AVG_PAGE, AVG_REQUEST, AVG_TRANSACTION_RT, BINARY_DATA,
        TEST_TYPE, TEST_RUN_NO, MAIL_HTML, PASSED_CONDITION) 
    values(
        :APP_NAME, :ROW_ID, :APP_ABBR, :RELEASE_NAME, :USER_COUNT, 
        :RAMP_TIME, :EXPECTED_WPM, :URL, :APP_IP, :DB_IP, :APP_CORE,
        :APP_RAM, :DB_CORE, :DB_RAM, :OS_APP, :OS_DB, :APACHE_V, 
        :TOMCAT_V, :DB_V, :NL_MACHINE, :NL_MACHINE_PROCESSOR, 
        :NL_MACHINE_OS, :NL_V, :NL_MACHINE_CORE, :NL_MACHINE_SPEED,
        :NL_MACHINE_RAM, :NL_MACHINE_NW, :TEST_START, :TEST_END,
        :THROUGHPUT, :APP_CPU, :APP_MEM, :DB_CPU, :DB_MEM, 
        :TC_THREAD_COUNT, :LOGICAL_BLOCKS, :ACHIEVED_WPM, 
        :AVG_PAGE, :AVG_REQUEST, :AVG_TRANSACTION_RT, :BINARY_DATA, 
        :TEST_TYPE, :TEST_RUN_NO, :MAIL_HTML, :PASSED_CONDITION)'''
    try:
        APP_RAM = f'{float(gps.app_cores) * 4}'
    except:
        APP_RAM = 'NA'

    try:
        DB_RAM = f'{float(gps.db_cores) * 4}'
    except:
        DB_RAM = 'NA'

    sql_pt_results_run_result_format = {
        'ROW_ID': gps.pt_results_run_result_sequence,
        'APP_NAME': gps.app_full_name,
        'APP_ABBR': gps.app_name,
        'RELEASE_NAME': gps.release_name,
        'USER_COUNT': gps.number_of_users_in_test,
        'RAMP_TIME': gps.rampup_time_secs,
        'EXPECTED_WPM': gps.wpm_required,
        'URL': url,
        'APP_IP': gps.app_IP,
        'DB_IP': gps.db_IP,
        'APP_CORE': gps.app_cores,
        'APP_RAM': APP_RAM,
        'DB_CORE': gps.db_cores,
        'DB_RAM': DB_RAM,
        'OS_APP': re.compile(r'PRETTY_NAME="(.*?)"').findall(
            gps.ssh_app.exec_command('cat /etc/os-release')[1].read().decode())[0],
        'OS_DB': re.compile(r'PRETTY_NAME="(.*?)"').findall(
            gps.ssh_app.exec_command('cat /etc/os-release')[1].read().decode())[0],
        'APACHE_V': apache_v,
        'TOMCAT_V': re.compile(r'Apache Tomcat Version ([0-9.]+)').findall(tomcat_release_notes)[0],
        'DB_V': re.compile(r'----+[\s]*(.*)[\s]').findall(db_v_cmd_out)[0],
        'NL_MACHINE': gps.execution_IP,
        'NL_MACHINE_PROCESSOR': nl_cpu_name,
        'NL_MACHINE_OS': nl_os_name,
        'NL_V': re.compile(r'product.version=([0-9.]+)\s').findall(nlp_file)[0],
        'NL_MACHINE_CORE': nl_cores,
        'NL_MACHINE_SPEED': nl_cpu_speed,
        'NL_MACHINE_RAM': f'{nl_ram}',
        'NL_MACHINE_NW': f'{nl_nw_speed}',
        'TEST_START': gps.test_start_time,
        'TEST_END': gps.test_stop_time,
        'THROUGHPUT': gps.avg_throughput_ps,
        'APP_CPU': gps.app_cpu_util,
        'APP_MEM': gps.app_mem_util,
        'DB_CPU': gps.db_cpu_util,
        'DB_MEM': gps.db_mem_util,
        'TC_THREAD_COUNT': gps.tc_thread_count,
        'LOGICAL_BLOCKS': gps.logical_blocks,
        'ACHIEVED_WPM': f'{gps.wpm_achieve}',
        'AVG_PAGE': gps.avg_pages_ps,
        'AVG_REQUEST': gps.avg_req_s_ps,
        'AVG_TRANSACTION_RT': gps.avg_txn_rt,
        'BINARY_DATA': images_folder_zip_cont,
        'TEST_TYPE': gps.test_type,
        'TEST_RUN_NO': int(gps.run),
        'MAIL_HTML': zip_html_mail_content,
        'PASSED_CONDITION': gps.test_status
    }

    all_loggers.logger_log.info(f'sql_pt_results_run_result_format: {sql_pt_results_run_result_format}')
    gps.global_cursor.execute(sql_pt_results_run_result, sql_pt_results_run_result_format)

    # app_name = gps.app_full_name
    # app_abbr = gps.app_name
    # release = gps.release_name
    # user_count = gps.number_of_users_in_test
    # rampup_time = gps.rampup_time_secs
    # expected_wpm = gps.wpm_required
    # url = re.compile(r'[\n][ ]*ServerName ([a-zA-Z0-9.:-_]*)').findall(httpd_file)[0]
    # app_ip = gps.app_IP
    # db_ip = gps.db_IP
    # app_core = gps.app_cores
    # db_core = gps.db_cores
    # os_app = re.compile(r'PRETTY_NAME="(.*?)"').findall(
    # gps.ssh_app.exec_command('cat /etc/os-release')[1].read().decode())[0]
    # os_db = re.compile(r'PRETTY_NAME="(.*?)"').findall(
    # gps.ssh_app.exec_command('cat /etc/os-release')[1].read().decode())[0]
    #
    # apache_v = re.compile(r' Apache/([0-9.]+) ').findall(req.get(f'{url}/server-status?auto', verify=False).text)
    # tomcat_v = re.compile(r'Apache Tomcat Version ([0-9.]+)').findall(tomcat_release_notes)[0]
    # db_v = re.compile(r'----+[\s]*(.*)[\s]').findall(db_v_cmd_out)[0]
    # nl_machine = gps.execution_IP
    # nl_machine_processor = nl_cpu_name
    # nl_machine_os = nl_os_name
    # nl_v = re.compile(r'product.version=([0-9.]+)\s').findall(nlp_file)[0]
    #
    # nl_machine_core = nl_cores
    # nl_machine_speed = nl_cpu_speed
    # nl_machine_ram = nl_ram
    # nl_machine_nw = nl_nw_speed
    # test_start = gps.test_start_time
    # test_end = gps.test_stop_time
    # throughput = gps.avg_throughput_ps
    # app_cpu = gps.app_cpu_util
    # app_mem = gps.app_mem_util
    # db_cpu = gps.db_cpu_util
    # db_mem = gps.db_mem_util
    # tc_thread_count = gps.tc_thread_count
    # logical_blocks = gps.logical_blocks
    # achieved_wpm = gps.wpm_achieve
    # avg_page = gps.avg_pages_ps
    # avg_request = gps.avg_req_s_ps
    # avg_transaction_rt = gps.avg_txn_rt
    # binary_data = images_folder_zip_cont
    # test_type = gps.test_type
    # test_run_no = gps.run
    # mail_html = html_mail_content
    # passed_condition = gps.test_status

    ''' End New code for pt_results_run_result'''

    data = {
        'key': 'ramnarayanbajabajata',
        'msg': html_mail_content,
        'from': 'rajveer.singh.metricstream@gmail.com',
        'to': ';'.join(gps.to_mail_file),
        # 'to': ';'.join([k.decode().strip() for k
        # in open("Clients/to_mail_file.txt", "rb").readlines()]),
        'subject': f"Performance Test Results - {gps.app_name} - {gps.release_name}"
    }

    """Revisit the Code
    
    
    '''EXECUTION SUMMARY TABLE'''

    ssh_app = SSHClient()
    ssh_app.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_app.connect(gps.app_IP, port=22, username='oracle', password='oracle')
    # pid = ssh_app.exec_command('ps a | less | grep Duser')[1].read().decode().split(' ', 1)[1].split(' ', 1)[0]
    # print(pid)
    ssh_app.close()

    '''THREAD DUMP'''
    '''bash jstack_ThreadAutomate.sh 12895'''
    '''MANUALLY'''

    '''HEAP DUMP'''

    sql = "select JDK_PATH from plab_servers_t where app = '{}'".format(
        gps.app_name)

    gps.global_cursor.execute(sql)
    jdk = gps.global_cursor.fetchall()
    jdk_location = jdk[0][0]
    dump_name = 'heap_dump_%s.hprof' % str(
        dt.now().strftime('%Y-%m-%d_%H-%M-%S'))
    dump_location = gps.heap_dump_location + r'/' + dump_name
    heap_dump_command = jdk_location + \
        ' -dump:live,format=b,file=' + dump_name  # + ' ' + pid
    '''/data/jdk1.8.0_45/bin/jmap -dump:live,format=b,file=/data/new_files/heap_dump.hprof 6861'''
    # print(heap_dump_command)

    '''  DOWNLOAD XML EXECUTION   '''

    sql = "SELECT WINDOWS_IP FROM PLAB_SERVERS_T where APP = '{}'".format(
        gps.app_name)
    gps.global_cursor.execute(sql)
    windows_ip_s = gps.global_cursor.fetchall()
    windows_ip_sum = windows_ip_s[0][0]

    url_g = "http://%s:7400/Results/v1/Service.svc/GenerateReport" % windows_ip_sum
    url_d = "http://%s:7400/Results/v1/Service.svc/DownloadReport" % windows_ip_sum
    data_sum = {"d": {"Format": "XML",
                      'CustomReportContents': True, "FileName": 'Execution.xml'}}
    data_sum = json.dumps(data_sum)
    headers = {'Content-type': 'application/json'}
    resp = requests.post(url_g, data=data_sum, headers=headers)

    count = 0
    while resp.status_code != 201:
        count += 1
        if count == 100:
            raise Exception(
                'Status code{} not Zero for {}@{} as {}'.format(resp.status_code, windows_ip_sum, 'Execution.xml',
                                                                resp.text))
        time.sleep(5)

    repid = (json.loads(resp.text))["d"]["ReportId"]

    data_sum = {"d": {"ReportId": repid}}
    data_sum = json.dumps(data_sum)

    resp = requests.post(url_d, data=data_sum, headers=headers)
    while not str(resp.status_code) == '201':
        resp = requests.post(url_d, data=data_sum, headers=headers)
        time.sleep(3)

    open('Execution.xml', 'wb').write(resp.content)

    '''ENDING HERE'''

    xml_file = r"Execution.xml"

    tree = Et.parse(xml_file)
    root = tree.getroot()

    data_for_closure = dict()

    '''EXECUTION'''
    for child in root.iter('statistic'):
        # print(child.attrib['name']+'->'+ child.attrib['value']+child.attrib['unit'])
        data_for_closure[child.attrib['name']
                         ] = child.attrib['value'] + child.attrib['unit']

    for child in root.iter('rampuppolicy'):
        RAMP_UP_POLICY = 'From %s users, adding %s users  every %s%s, to a maximum of %s users.' % (
            child.attrib['from'], child.attrib['add'], child.attrib['interval'], child.attrib['unit'],
            child.attrib['max'])
        RAMP_UP_TIME = str(int((((int(child.attrib['max']) - int(child.attrib['from'])) / int(
            child.attrib['add'])) * float(child.attrib['interval'])) / 60)) + ' minutes and ' + str(int((((int(
                child.attrib['max']) - int(child.attrib['from'])) / int(child.attrib['add'])) * float(
                child.attrib['interval'])) % 60)) + ' seconds'
        data_for_closure['RAMP_UP_TIME'] = RAMP_UP_TIME
        data_for_closure['RAMP_UP_POLICY'] = RAMP_UP_POLICY

    os.remove('Execution.xml')

    '''MONITOR'''

    url_g = "http://%s:7400/Results/v1/Service.svc/GenerateReport" % gps.monitor_IP
    url_d = "http://%s:7400/Results/v1/Service.svc/DownloadReport" % gps.monitor_IP
    data_sum = {"d": {"Format": "XML",
                      'CustomReportContents': True, "FileName": 'Monitor.xml'}}
    data_sum = json.dumps(data_sum)
    headers = {'Content-type': 'application/json'}
    resp = requests.post(url_g, data=data_sum, headers=headers)

    count = 0
    while resp.status_code != 201:
        count += 1
        if count == 100:
            raise Exception(
                'Status code{} not Zero for {}@{} as {}'.format(resp.status_code, gps.monitor_IP, 'Monitor.xml',
                                                                resp.text))
        time.sleep(5)

    repid = (json.loads(resp.text))["d"]["ReportId"]

    data_sum = {"d": {"ReportId": repid}}
    data_sum = json.dumps(data_sum)

    resp = requests.post(url_d, data=data_sum, headers=headers)
    while not str(resp.status_code) == '201':
        resp = requests.post(url_d, data=data_sum, headers=headers)
        time.sleep(3)

    open('Monitor.xml', 'wb').write(resp.content)

    xml_file = r"Monitor.xml"

    tree = Et.parse(xml_file)
    root = tree.getroot()

    used_max = ''
    used_total = ''

    cpu_user = ''
    cpu_system = ''

    used_max_db = ''
    used_total_db = ''

    cpu_user_db = ''
    cpu_system_db = ''

    app_fancy = ''
    db_fancy = ''
    sql = 'select * from plab_servers_fancy_keys_t'
    gps.global_cursor.execute(sql)

    a = gps.global_cursor.fetchall()

    for i in a:
        if i[1] == gps.app_IP:
            app_fancy = (i[0])

        if i[1] == gps.db_IP:
            db_fancy = (i[0])

    for child in root.iter('statistic-item'):
        if child.attrib['name'] == 'Controller/Thread Count':
            data_for_closure['THREAD_COUNT'] = child.attrib['avg']

        elif child.attrib['name'] == f'{db_fancy}/oracleDB/Logical IO/Block changes':
            data_for_closure['LOGICAL_IO_BLOCK_CHANGES'] = child.attrib['avg']

        elif child.attrib['name'] == f'{app_fancy}/linux/Memory/Memory Used':
            used_max = float(float(child.attrib['max'].replace(',', '')) * 100)

        elif child.attrib['name'] == f'{app_fancy}/linux/Memory/Memory Total':
            used_total = float(float(child.attrib['max'].replace(',', '')))

        elif child.attrib['name'] == f'{app_fancy}/linux/System/CPU User':
            cpu_user = float(child.attrib['avg'])

        elif child.attrib['name'] == f'{app_fancy}/linux/System/CPU System':
            cpu_system = float(child.attrib['avg'])

        elif child.attrib['name'] == f'{db_fancy}/Linux/Memory/Memory Used':
            used_max_db = float(
                float(child.attrib['max'].replace(',', '')) * 100)

        elif child.attrib['name'] == f'{db_fancy}/Linux/Memory/Memory Total':
            used_total_db = float(float(child.attrib['max'].replace(',', '')))

        elif child.attrib['name'] == f'{db_fancy}/Linux/System/CPU User':
            cpu_user_db = float(child.attrib['avg'])

        elif child.attrib['name'] == f'{db_fancy}/Linux/System/CPU System':
            cpu_system_db = float(child.attrib['avg'])

    data_for_closure['APP_CORE_UTILIZED'] = round(cpu_system + cpu_user, 2)
    data_for_closure['APP_MEM_UTILIZED'] = round(used_max / used_total, 2)

    data_for_closure['DB_CORE_UTILIZED'] = round(
        float(cpu_system_db) + float(cpu_user_db), 2)
    data_for_closure['DB_MEM_UTILIZED'] = round(used_max_db / used_total_db, 2)

    os.remove('Monitor.xml')
    # for i, j in data_for_closure.items():
    #     print(i, j)

    APP_NAME = gps.app_name
    TEST_RUN_NO = gps.run
    TEST_TYPE = gps.test_type
    RELEASE_NAME = gps.release_name
    TEST_DATE = gps.test_start_time
    TEST_STATUS = test_status_summary
    LOAD_PERCENTAGE = int(
        round(int(gps.number_of_users_in_test) * 100 / int(gps.total_users), 2))

    os.environ['Path'] = 'Clients/instantclient_11_2;Clients/instantclient_12_1;Clients/instantclient_18_5'
    cs = '{schema_name}/{schema_pwd}@{db_IP}:{port}/{db_id}'.format(schema_name=gps.schema_name,
                                                                    schema_pwd=gps.schema_pwd, db_IP=gps.db_IP,
                                                                    port=gps.oracle_db_port, db_id=gps.oracle_db_id)
    installer_summary = ''
    with cx_Oracle.connect(cs) as conn:
        with conn.cursor() as cursor:
            query = '''
                        SELECT MODULE_NAME, INSTALLER_NAME, VERSION FROM SI_VERSION_INFO WHERE INSTALLER_ID IN 
                        (SELECT MAX(INSTALLER_ID) FROM SI_VERSION_INFO GROUP BY Module_name) AND 
                        MODULE_NAME NOT IN({avoid_me}) 
                        ORDER BY MODULE_NAME
                        '''
            with open('Clients/installers_to_avoid.txt', 'rb') as f:
                installers = f.read().decode().split(',')
                avoid_me = "'dummy"
                for installer in installers:
                    if len(installer.strip()) > 0:
                        avoid_me += "','" + installer.strip()
                avoid_me += "'"
            cursor.execute(query.format(avoid_me=avoid_me))
            rows = cursor.fetchall()

            installers_sum = list()
            for row in rows:
                installers_sum.append(row[0] + '_' + row[1] + '_' + row[2])
            installer_summary = json.dumps(installers_sum)

    INSTALLERS = installer_summary
    SCENARIOS_COUNT = scn_count
    EXPECTED_WPM = gps.wpm_required
    ACTIVE_USERS = gps.number_of_users_in_test
    CONCURRENT_USERS = gps.number_of_users_in_test

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(gps.app_IP, port=22, username='oracle',
                password=gps.App_Oracle_PWD)
    _, outt, err = ssh.exec_command('nproc')
    cores = str(outt.readlines()[0].strip())
    ram = 4 * int(cores)
    ssh.close()
    app_core, app_memory = str(cores), str(ram)

    APP_CORE_ALLOCATED = app_core
    APP_MEM_ALLOCATED = app_memory

    ssh.connect(gps.db_IP, port=22, username='oracle',
                password=gps.DB_Oracle_PWD)
    _, outt, _ = ssh.exec_command('nproc')
    cores = str(outt.readlines()[0].strip())
    ram = 4 * int(cores)
    ssh.close()
    db_core, db_memory = str(cores), str(ram)

    DB_CORE_ALLOCATED = db_core
    DB_MEM_ALLOCATED = db_memory

    APP_CORE_UTILIZED = data_for_closure['APP_CORE_UTILIZED']
    APP_MEM_UTILIZED = data_for_closure['APP_MEM_UTILIZED']
    DB_CORE_UTILIZED = data_for_closure['DB_CORE_UTILIZED']
    DB_MEM_UTILIZED = data_for_closure['DB_MEM_UTILIZED']

    ACHIEVED_WPM = gps.wpm_achieve
    TOTAL_TRANSACTIONS = total_txns_summary
    TOTAL_FAILED_TRANSACTIONS = failed_txns_summary
    TEST_DURATION = str(gps.test_stop_time - gps.test_start_time)
    THROUGHPUT = data_for_closure['avg_throughput']
    HITS_PER_SEC = data_for_closure['avg_hits/s']
    THREAD_COUNT = data_for_closure['THREAD_COUNT']
    LOGICAL_IO_BLOCK_CHANGES = data_for_closure['LOGICAL_IO_BLOCK_CHANGES']
    TEST_SCOPE = test_scope_summary

    with open("Clients/changes_made.txt", "r") as f:
        changes_made_summary = f.readlines()

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
    (APP_NAME, TEST_RUN_NO, TEST_TYPE, RELEASE_NAME, TEST_DATE, TEST_STATUS, LOAD_PERCENTAGE, INSTALLERS,
     SCENARIOS_COUNT, 
    EXPECTED_WPM, ACTIVE_USERS, CONCURRENT_USERS, APP_CORE_ALLOCATED, APP_MEM_ALLOCATED, DB_CORE_ALLOCATED, 
    DB_MEM_ALLOCATED,
    APP_CORE_UTILIZED, APP_MEM_UTILIZED, DB_CORE_UTILIZED, DB_MEM_UTILIZED, ACHIEVED_WPM, TOTAL_TRANSACTIONS,
      TOTAL_FAILED_TRANSACTIONS, TEST_DURATION, THROUGHPUT, HITS_PER_SEC, THREAD_COUNT, LOGICAL_IO_BLOCK_CHANGES, 
      TEST_SCOPE, CHANGES_MADE, REMARKS, AVG_PAGE_PER_SEC, AVG_REQ_RESP_TIME, RAMP_UP_TIME, SVN_PATH, RAMP_UP_POLICY, 
      ROW_ID, HEAP_DUMP_LOCATION, THREAD_DUMP_LOCATION)
    VALUES
    (:APP_NAME, :TEST_RUN_NO, :TEST_TYPE, :RELEASE_NAME, :TEST_DATE, :TEST_STATUS, :LOAD_PERCENTAGE, :INSTALLERS, 
    :SCENARIOS_COUNT, :EXPECTED_WPM, :ACTIVE_USERS, :CONCURRENT_USERS, :APP_CORE_ALLOCATED, :APP_MEM_ALLOCATED, 
    :DB_CORE_ALLOCATED, :DB_MEM_ALLOCATED, :APP_CORE_UTILIZED, :APP_MEM_UTILIZED, :DB_CORE_UTILIZED, :DB_MEM_UTILIZED, 
    :ACHIEVED_WPM, :TOTAL_TRANSACTIONS, :TOTAL_FAILED_TRANSACTIONS, :TEST_DURATION, :THROUGHPUT, :HITS_PER_SEC, 
    :THREAD_COUNT, :LOGICAL_IO_BLOCK_CHANGES, :TEST_SCOPE, :CHANGES_MADE, :REMARKS, :AVG_PAGE_PER_SEC, 
    :AVG_REQ_RESP_TIME,
    :RAMP_UP_TIME, :SVN_PATH, :RAMP_UP_POLICY, execution_summary_seq.NEXTVAL, :HEAP_DUMP_LOCATION, 
    :THREAD_DUMP_LOCATION)
    '''

    format_sql = {
        'APP_NAME': str(APP_NAME),
        'TEST_RUN_NO': int(TEST_RUN_NO),
        'TEST_TYPE': str(TEST_TYPE),
        'RELEASE_NAME': str(RELEASE_NAME),
        'TEST_DATE': TEST_DATE,
        'TEST_STATUS': str(TEST_STATUS),
        'LOAD_PERCENTAGE': str(LOAD_PERCENTAGE),
        'INSTALLERS': str(INSTALLERS),
        'SCENARIOS_COUNT': str(SCENARIOS_COUNT),
        'EXPECTED_WPM': str(EXPECTED_WPM),
        'ACTIVE_USERS': str(ACTIVE_USERS),
        'CONCURRENT_USERS': str(CONCURRENT_USERS),
        'APP_CORE_ALLOCATED': str(APP_CORE_ALLOCATED),
        'APP_MEM_ALLOCATED': str(APP_MEM_ALLOCATED),
        'DB_CORE_ALLOCATED': str(DB_CORE_ALLOCATED),
        'DB_MEM_ALLOCATED': str(DB_MEM_ALLOCATED),
        'APP_CORE_UTILIZED': str(APP_CORE_UTILIZED),
        'APP_MEM_UTILIZED': str(APP_MEM_UTILIZED),
        'DB_CORE_UTILIZED': str(DB_CORE_UTILIZED),
        'DB_MEM_UTILIZED': str(DB_MEM_UTILIZED),
        'ACHIEVED_WPM': str(ACHIEVED_WPM),
        'TOTAL_TRANSACTIONS': str(TOTAL_TRANSACTIONS),
        'TOTAL_FAILED_TRANSACTIONS': str(TOTAL_FAILED_TRANSACTIONS),
        'TEST_DURATION': str(TEST_DURATION),
        'THROUGHPUT': str(THROUGHPUT),
        'HITS_PER_SEC': str(HITS_PER_SEC),
        'THREAD_COUNT': str(THREAD_COUNT),
        'LOGICAL_IO_BLOCK_CHANGES': str(LOGICAL_IO_BLOCK_CHANGES),
        'TEST_SCOPE': str(TEST_SCOPE),
        'CHANGES_MADE': str(CHANGES_MADE),
        'REMARKS': str(REMARKS),
        'AVG_PAGE_PER_SEC': str(AVG_PAGE_PER_SEC),
        'AVG_REQ_RESP_TIME': str(AVG_REQ_RESP_TIME),
        'RAMP_UP_TIME': str(RAMP_UP_TIME),
        'SVN_PATH': str(SVN_PATH),
        'RAMP_UP_POLICY': str(RAMP_UP_POLICY),
        'HEAP_DUMP_LOCATION': str(HEAP_DUMP_LOCATION),
        'THREAD_DUMP_LOCATION': str(THREAD_DUMP_LOCATION)
    }

    gps.global_cursor.execute(sql, format_sql)

    Revisit the Code"""
    url = gps.mail_api

    print('Requesting for mail to send...')

    resp = requests.post(url, data=data)
    print(resp.text)

except Exception as e:

    all_loggers.logger_log.info('Failed to send the mail')
    all_loggers.logger_log.exception(e)

    print('Failed to send the mail')
    data = {
        'key': 'ramnarayanbajabajata',
        'msg': '<h1> Failed to send the Mail.</h1><p>{}</p>'.format(e),
        'from': 'rajveer.singh.metricstream@gmail.com',
        # 'to': ';'.join([k.decode().strip() for k in open("Clients/to_mail_file.txt", "rb").readlines()]),
        'to': ';'.join(gps.to_mail_file),
        'subject': "Failed to Send For - {app} - {release} - Run - {run}".format(app=gps.app_name,
                                                                                 release=gps.release_name,
                                                                                 run=gps.run)
    }

else:

    all_loggers.logger_log.info('trying to commit')
    gps.global_conn.commit()
    all_loggers.logger_log.info('committed as no errors found')

finally:
    all_loggers.logger_log.info('Executing Finally block')
    print('Process Done')
    try:
        gps.global_cursor.close()
    except:
        pass
    try:
        gps.global_conn.close()
    except:
        pass
    try:
        gps.sftp_db.close()
    except:
        pass
    try:
        gps.ssh_db.close()
    except:
        pass
    try:
        gps.sftp_app.close()
    except:
        pass
    try:
        gps.ssh_app.close()
    except:
        pass
    try:
        gps.rce.remove_service()
    except:
        pass
    try:
        gps.rce.disconnect()
    except:
        pass

    all_loggers.logger_log.info('Executed Finally block')
    all_loggers.logger_log.info('stopping the tool')
