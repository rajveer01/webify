import logging
import os
import sys
import requests

"""
'python',
1 => app_name,                  # App name
2 => tool_dir,                  # tool directory to change CW directory
3 => rel_run_logs_folder,       # Relative to tools directory for run logs
4 => json_file_name,            # Json File for Parameters under the folder Run Logs
5 => log_file_name,             # log file name for logs
6 => stdout_file,               # output file name to log std output 
7 => stderr_file,               # error file name to log std errors
"""

args = sys.argv

if len(args) < 8:
    print(f'Exception Not Called with Proper parameters {args}')
    raise Exception(f'Not Called with Proper parameters {args}')

tool_dir = str(args[2]).strip()
rel_run_logs_folder = str(args[3]).strip()
log_file_name = str(args[5]).strip()
stdout_file = str(args[6]).strip()
stderr_file = str(args[7]).strip()

# requests.get(f'http://127.0.0.1:8000/nl_project_manager/print_me/?text=Now{tool_dir}').close()
# requests.get(f'http://127.0.0.1:8000/nl_project_manager/print_me/?text=Now{rel_run_logs_folder}').close()
# requests.get(f'http://127.0.0.1:8000/nl_project_manager/print_me/?text=Now{log_file_name}').close()
# requests.get(f'http://127.0.0.1:8000/nl_project_manager/print_me/?text=Now{stdout_file}').close()
# requests.get(f'http://127.0.0.1:8000/nl_project_manager/print_me/?text=Now{stderr_file}').close()


format_log = '''
%(levelname)s - %(asctime)s
    File: %(filename)s 
    Line: %(lineno)d
    Func: %(funcName)s
    MSG: %(message)s
'''


format_stdout = '%(message)s'
format_stderr = '%(message)s'

web_server_dir = os.getcwd()
os.chdir(tool_dir)


logger_log = logging.getLogger('logger_log')
logger_log.setLevel(logging.INFO)

formatter_log = logging.Formatter(format_log)

file_handler_log = logging.FileHandler(f"{rel_run_logs_folder}/{log_file_name}", mode='w')
file_handler_log.setFormatter(formatter_log)
logger_log.addHandler(file_handler_log)

logger_stdout = logging.getLogger('logger_stdout')
logger_stdout.setLevel(logging.INFO)

formatter_stdout = logging.Formatter(format_stdout)

file_handler_stdout = logging.FileHandler(f"{rel_run_logs_folder}/{stdout_file}", mode='w')
file_handler_stdout.setFormatter(formatter_stdout)

logger_stdout.addHandler(file_handler_stdout)


logger_stderr = logging.getLogger('logger_stderr')
logger_stderr.setLevel(logging.INFO)

formatter_stderr = logging.Formatter(format_stderr)

file_handler_stderr = logging.FileHandler(f"{rel_run_logs_folder}/{stderr_file}", mode='w')
file_handler_stderr.setFormatter(formatter_stderr)

logger_stderr.addHandler(file_handler_stderr)


'''
3 Loggers Have been set to log things,
    root logger for logging info,
    logger_stdout for output logging
    logger_stderr for error logging
'''


class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        self.logger.log(self.log_level, buf.rstrip().strip())

    def flush(self):
        pass


sys.stdout = StreamToLogger(logger_stdout, logging.INFO)
sys.stderr = StreamToLogger(logger_stderr, logging.ERROR)
