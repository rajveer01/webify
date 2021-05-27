import win32net
from unidecode import unidecode as ucd
import pb
import all_loggers
import gps
import os


def mount(mount_folder):
    if not os.path.exists(mount_folder):
        try:
            username = gps.windows_user_name
            password = gps.windows_user_pwd
            all_loggers.logger_log.info(f'Trying to mount folder {mount_folder} @{username, password}')

            use_dict = dict()
            mount_folder = str(mount_folder).strip().replace('\\', '/')
            use_dict['remote'] = ucd(mount_folder)
            use_dict['password'] = ucd(password)
            use_dict['username'] = ucd(username)

            win32net.NetUseAdd(None, 2, use_dict)
        except Exception as e:
            print(pb.exp, f"Can't Mount the Directory for {e}")
            all_loggers.logger_log.exception(e)

