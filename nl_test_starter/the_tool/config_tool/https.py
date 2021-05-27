import paramiko
import all_loggers


logging = all_loggers.logger_log


def ssl(app_ip,username_app,pwd_ap,SYSTEMi,schema_psw):
    ssh_app = paramiko.SSHClient()
    ssh_app.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_app.connect(app_ip, username=username_app, password=pwd_ap)
    sftp_app = ssh_app.open_sftp()

    file_ms_installer_path = SYSTEMi[0:-7]
    ms_installer_properties_file = file_ms_installer_path +'/metricstream-installer-app/ms-installer-parameters.properties'


    with sftp_app.open(ms_installer_properties_file) as prop_file:
        data = prop_file.readlines()
        # new_data = ''

        for line in data:
            # data_as_list = line.split('=', 1)
            if 'SslConfigurationFlag' in line:
                data_yn = line.split('SslConfigurationFlag=')[1]
                if 'No'in data_yn:

                    S99_comm_stop = SYSTEMi + '/Systemi/bin/S99systemi.sh stop'  # command to stop services
                    _, output, _ = ssh_app.exec_command(S99_comm_stop)  # to store the input,output,eror values of command
                    print(output.read().decode())
                    logging.info("executed the command to stop app services")

                    file_ms_installer_path = SYSTEMi[0:-7]  # block of code to handle ms_installer_properties_file
                    ms_installer_properties_file = file_ms_installer_path + '/metricstream-installer-app/ms-installer-parameters.properties'

                    with sftp_app.open(ms_installer_properties_file) as prop_file:
                        data = prop_file.readlines()
                        print(data)
                        new_data = ''
                        for line in data:
                            data_as_list = line.split('=', 1)
                            if data_as_list[0].strip() == 'SslConfigurationFlag':
                                data_as_list[1] = 'Yes'
                                line = data_as_list[0] + '=' + str(data_as_list[1]) + '\n'
                            new_data += line
                    with sftp_app.open(ms_installer_properties_file, 'wb') as prop_file:
                        prop_file.write(new_data)
                        logging.info("Changed SslConfigurationFlag from No to Yes")

                    file_httpd_conf = SYSTEMi + '/Apache/conf/httpd.conf'
                    with sftp_app.open(file_httpd_conf) as apache:
                        data = apache.readlines()
                        new_data = ''
                        for line in data:
                            if '#Include conf/extra/httpd-ssl.conf' in line:
                                line = line.replace("#Include conf/extra/httpd-ssl.conf", 'Include conf/extra/httpd-ssl.conf')
                            new_data += line
                            logging.info("Un commented the line 'Include conf/extra/httpd-ssl.conf'")
                    with sftp_app.open(file_httpd_conf, 'wb') as apache:
                        apache.write(new_data)
                    stdin, output, error = ssh_app.exec_command(
                        f'cd {file_ms_installer_path}/metricstream-installer-app; ./ms-installer.sh -ssl -p {schema_psw}')  # installer file
                    stdin.write('\n')
                    stdin.flush()
                    print(output.read().decode())
                    logging.info("executed the './ms-installer.sh -ssl -p password' command")

                    stdin, output, error = ssh_app.exec_command(
                        f'cd {file_ms_installer_path}/metricstream-installer-app; ./ms-installer.sh -genDemoCrt')
                    stdin.write('\n')
                    stdin.write(f'{app_ip}')
                    stdin.write('IN')
                    stdin.write('KAR')
                    stdin.write('BLR')
                    logging.info("executed the './ms-installer.sh -genDemoCrt' command")


                    S99_comm_start = SYSTEMi + '/Systemi/bin/S99systemi.sh start'  # command to start services
                    _, output, _ = ssh_app.exec_command(S99_comm_start)
                    print(output.read().decode())
                    ssh_app.close()
                    logging.info("executed the command to start app services")
                    return 'instance is converted from http --> https '

                else:
                    return 'The instance is already SSL Configured'