import all_loggers
import os
import time


def get_index_file(arbitrary_res_folder):

    try:
        result_folder = arbitrary_res_folder
        all_loggers.logger_log.info(f'Trying to find the latest folder in: {result_folder}')
        latest_folder = max([os.path.join(result_folder, d) for d in os.listdir(result_folder)], key=os.path.getmtime)
        summary_file = latest_folder + r"\summary\index.html"

        while not os.path.exists(summary_file):
            latest_folder = max([os.path.join(result_folder, d) for d in os.listdir(result_folder)],
                                key=os.path.getmtime)

            summary_file = latest_folder + r"\summary\index.html"
            all_loggers.logger_log.info('Waiting For Latest Folder and index.html in it.')
            time.sleep(5)
        all_loggers.logger_log.info(f'Found the Latest folder as: {latest_folder} and Index file as {summary_file}')
        return latest_folder, summary_file
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
