import win32net
from unidecode import unidecode as unicode
import os


def get_dir_list(selected, ip):

    username = 'administrator'
    password = 'welcome*123'

    root_folder = selected

    if '$' not in selected:
        drives = win32net.NetServerDiskEnum(ip, 0)
        drives = [drive.replace(':', '$') for drive in drives]
        x = [r'{selected}/{drive}'.format(selected=selected, drive=drive) for drive in drives]
        return selected, x

    use_dict = dict()

    root_folder = str(root_folder).strip().replace('\\', '/')
    use_dict['remote'] = unicode(root_folder)
    use_dict['password'] = unicode(password)
    use_dict['username'] = unicode(username)

    win32net.NetUseAdd(None, 2, use_dict)

    for root, dirnames, filenames in os.walk(root_folder):
       dirs = [os.path.join(root, dirname).replace('\\', '/').rstrip('/') for dirname in dirnames]
       files = [os.path.join(root, filename).replace('\\', '/').rstrip('/') for filename in filenames]
       return root.rstrip('/'), dirs + files
