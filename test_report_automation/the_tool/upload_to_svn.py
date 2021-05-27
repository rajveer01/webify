import all_loggers
import os

import svn.remote

import gps


def copy(from_file):
    try:
        to_file = gps.svn_artifact_folder + '/' + os.path.basename(from_file)
        all_loggers.logger_log.info(f'Enter copy() function to upload in SVN, From: {from_file} to {to_file}')
        client = svn.remote.RemoteClient(url=to_file, username=gps.svn_user_name, password=gps.svn_password)
        k = client.run_command('import', [from_file,
                                          to_file,
                                          # '--username',
                                          # 'ashokkumar',
                                          # '--password',
                                          # 'performance@2019',
                                          '-m',
                                          'try'])
        all_loggers.logger_log.info(f'Copied to SVN with Response: {k}')
        return to_file
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
