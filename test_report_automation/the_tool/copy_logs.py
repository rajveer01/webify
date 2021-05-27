import all_loggers
import os
from datetime import datetime as dt

import paramiko
from paramiko import SSHClient

import gps
from directory_downloader import download as download_dir


def ts():
    return round(dt.timestamp(dt.now()))


def copy():
    def exp_writer(a_type, agent, file_name, exp):
        with open(os.path.join(artifacts_folder + rf"\Additional Files\failed_to_collected.txt", 'a')) as f:
            f.write(f'Failed to collect {a_type} from {agent}	{file_name}	because	{exp}\n')

    try:
        all_loggers.logger_log.info('Enter into copy() function to copy logs.')
        artifacts_folder = gps.artifacts_folder

        all_loggers.logger_log.info(
            f'Trying to connect to the App {gps.app_IP} with {gps.user}/{gps.App_Oracle_PWD} for Logs')
        all_loggers.logger_log.info(
            f'Trying to connect to the DB {gps.db_IP} with {gps.user}/{gps.DB_Oracle_PWD} for Logs')

        gps.ssh_app = SSHClient()
        gps.ssh_db = SSHClient()
        gps.ssh_app.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gps.ssh_db.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        gps.ssh_app.connect(gps.app_IP, port=22, username=gps.user, password=gps.App_Oracle_PWD)
        gps.ssh_db.connect(gps.db_IP, port=22, username=gps.user, password=gps.DB_Oracle_PWD)

        gps.sftp_app = gps.ssh_app.open_sftp()
        gps.sftp_db = gps.ssh_db.open_sftp()

        all_loggers.logger_log.info(f'Connected to both app and DB. Making Folders in {artifacts_folder}')

        os.makedirs(artifacts_folder + r"\Systemi\logs")
        os.makedirs(artifacts_folder + r"\Systemi\Config")
        os.makedirs(artifacts_folder + r"\Tomcat\logs")
        os.makedirs(artifacts_folder + r"\Tomcat\Config")
        os.makedirs(artifacts_folder + r"\Apache\logs")
        os.makedirs(artifacts_folder + r"\Apache\Config")
        os.makedirs(artifacts_folder + r"\DB")
        os.makedirs(artifacts_folder + r"\CONFIG_TOOL_ARTIFACTS")
        os.makedirs(artifacts_folder + r"\Additional Files")

        all_loggers.logger_log.info('Folders Created, opening SFTP connection to both SSHs.')

        gps.sftp_db.get(
            gps.db_home + "/dbs/initdb19c.ora",
            os.path.join(artifacts_folder + r"\DB\initdb19c.ora"),
        )
        gps.sftp_db.get(
            gps.db_home + "/dbs/spfiledb19.ora",
            os.path.join(artifacts_folder + r"\DB\spfiledb19.ora"),
        )

        for file in gps.additional_files_app:
            try:
                gps.sftp_app.get(file, os.path.join(artifacts_folder + rf"\Additional Files\{os.path.basename(file)}"))

            except Exception as e:
                exp_writer(a_type='File', agent='App', file_name=file, exp=e)

        for file in gps.additional_files_db:
            try:
                gps.sftp_db.get(file, os.path.join(artifacts_folder + rf"\Additional Files\{os.path.basename(file)}"))

            except Exception as e:
                exp_writer(a_type='File', agent='DB', file_name=file, exp=e)

        for folder in gps.additional_dirs_app:
            try:
                download_dir(ssh=gps.ssh_app,
                             sftp=gps.sftp_app,
                             server_dir_path=folder,
                             artifact_dir_path=os.path.join(artifacts_folder,
                                                            rf"\Additional Files\{os.path.basename(folder)} - {ts()}"))

            except Exception as e:
                exp_writer(a_type='Directory', agent='App', file_name=folder, exp=e)

        for folder in gps.additional_dirs_db:
            try:
                download_dir(ssh=gps.ssh_db,
                             sftp=gps.sftp_db,
                             server_dir_path=folder,
                             artifact_dir_path=os.path.join(artifacts_folder,
                                                            rf"\Additional Files\{os.path.basename(folder)} - {ts()}"))

            except Exception as e:
                exp_writer(a_type='Directory', agent='DB', file_name=folder, exp=e)


        all_loggers.logger_log.info(f'Copying Logs Now, Systemi Path is {gps.SystemI_Path}')

        config_tool_artifacts_folder = gps.sftp_app.listdir(f'{gps.SystemI_Path}/CONFIG_TOOL_ARTIFACTS')
        config_tool_artifacts_file_name = [_ for _ in config_tool_artifacts_folder if "OLD - " not in _][0]
        all_loggers.logger_log.info(f'config_tool_artifacts_file_name: {config_tool_artifacts_file_name}, Now Copying')

        gps.sftp_app.get(
            f'{gps.SystemI_Path}/CONFIG_TOOL_ARTIFACTS/{config_tool_artifacts_file_name}',
            os.path.join(artifacts_folder + fr"\CONFIG_TOOL_ARTIFACTS\{config_tool_artifacts_file_name}"),
        )

        systemi_home = gps.sftp_app.listdir(gps.SystemI_Path)
        for ele in systemi_home:
            if str(ele).upper() == "TOMCAT":
                tomcat = gps.SystemI_Path + "/" + ele
                all_loggers.logger_log.info(f'Copying form {tomcat}')
                tomcat_list = gps.sftp_app.listdir(tomcat)
                for ele_1 in tomcat_list:
                    if str(ele_1).upper() == "LOG" or str(ele_1).upper() == "LOGS":
                        tomcat_log = tomcat + "/" + ele_1

                        download_dir(ssh=gps.ssh_app,
                                     sftp=gps.sftp_app,
                                     server_dir_path=tomcat_log,
                                     artifact_dir_path=artifacts_folder + r"\Tomcat\logs")

                        # for filename in sorted(gps.sftp_app.listdir(tomcat_log)):
                        #     gps.sftp_app.get(
                        #         tomcat_log + "/" + filename,
                        #         artifacts_folder + r"\Tomcat\logs" + "\\" + filename)

                    if str(ele_1).upper() == "BIN":
                        tomcat_bin = tomcat + "/" + ele_1
                        gps.sftp_app.get(
                            tomcat_bin + "/" + "Tomcat.sh",
                            artifacts_folder + r"\Tomcat\Config\Tomcat.sh",
                        )
                    if str(ele_1).upper() == "CONF":
                        tomcat_conf = tomcat + "/" + ele_1
                        gps.sftp_app.get(
                            tomcat_conf + "/" + "context.xml",
                            artifacts_folder + r"\Tomcat\Config\context.xml",
                        )
                        gps.sftp_app.get(
                            tomcat_conf + "/" + "server.xml",
                            artifacts_folder + r"\Tomcat\Config\server.xml",
                        )
                        gps.sftp_app.get(
                            tomcat_conf + "/" + "workers.properties",
                            artifacts_folder + r"\Tomcat\Config\workers.properties",
                        )
                        gps.sftp_app.get(
                            tomcat_conf + "/" + "web.xml",
                            artifacts_folder + r"\Tomcat\Config\web.xml",
                        )
                        gps.sftp_app.get(
                            tomcat_conf + "/" + "mod_jk.conf",
                            artifacts_folder + r"\Tomcat\Config\mod_jk.conf",
                        )

            if str(ele).upper() == "APACHE":
                apache = gps.SystemI_Path + "/" + ele
                all_loggers.logger_log.info(f'Copying form {apache}')
                apache_list = gps.sftp_app.listdir(apache)
                for ele_1 in apache_list:
                    if str(ele_1).upper() == "LOG" or str(ele_1).upper() == "LOGS":
                        apache_log = apache + "/" + ele_1

                        download_dir(ssh=gps.ssh_app,
                                     sftp=gps.sftp_app,
                                     server_dir_path=apache_log,
                                     artifact_dir_path=artifacts_folder + r"\Apache\logs")

                        # for filename in sorted(gps.sftp_app.listdir(apache_log)):
                        #     gps.sftp_app.get(apache_log + "/" + filename,
                        #                      artifacts_folder + r"\Apache\logs" + "\\" + filename)

                    if str(ele_1).upper() == "CONF":
                        apache_conf = apache + "/" + ele_1
                        gps.sftp_app.get(
                            apache_conf + "/" + "httpd.conf",
                            artifacts_folder + r"\Apache\Config\httpd.conf",
                        )

            if str(ele).upper() == "SYSTEMI":
                systemi = gps.SystemI_Path + "/" + ele
                all_loggers.logger_log.info(f'Copying form {systemi}')
                systemi_list = gps.sftp_app.listdir(systemi)
                for ele_1 in systemi_list:
                    if str(ele_1).upper() == "LOG" or str(ele_1).upper() == "LOGS":
                        systemi_log = systemi + "/" + ele_1

                        download_dir(ssh=gps.ssh_app,
                                     sftp=gps.sftp_app,
                                     server_dir_path=systemi_log,
                                     artifact_dir_path=artifacts_folder + r"\Systemi\logs")

                        # for filename in sorted(gps.sftp_app.listdir(systemi_log)):
                        #     gps.sftp_app.get(
                        #         systemi_log + "/" + filename,
                        #         artifacts_folder + r"\Systemi\logs" + "\\" + filename)

                    if str(ele_1).upper() == "CONFIG":
                        systemi_conf = systemi + "/" + ele_1
                        gps.sftp_app.get(
                            systemi_conf + "/" + "config.client.xml",
                            artifacts_folder + r"\Systemi\Config\config.client.xml",
                        )
                        gps.sftp_app.get(
                            systemi_conf + "/" + "logback.xml",
                            artifacts_folder + r"\Systemi\Config\logback.xml",
                        )

        all_loggers.logger_log.info('Logs and Configurations Copy Complete')
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
