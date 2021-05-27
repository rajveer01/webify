from paramiko import SSHClient
from paramiko.sftp_client import SFTPClient
import all_loggers


def download(ssh: SSHClient, sftp: SFTPClient, server_dir_path: str, artifact_dir_path: str):
    """
    Zip the Directory,
    Download the zip,
    Delete the zip from server.
    :param ssh:
    :param sftp:
    :param server_dir_path: what directory to be downloaded
    :param artifact_dir_path: where to download the zip file
    :return:
    """
    zip_name = 'logs.zip'
    cmd_to_zip = f'''pushd {server_dir_path}
zip -r {zip_name} .
popd
'''

    _, out, _ = ssh.exec_command(cmd_to_zip)
    all_loggers.logger_log.debug(out.read().decode())
    out.channel.recv_exit_status()

    server_zip_path = f'{server_dir_path}/{zip_name}'

    sftp.get(server_zip_path, f'{artifact_dir_path}/{zip_name}')

    sftp.remove(server_zip_path)
