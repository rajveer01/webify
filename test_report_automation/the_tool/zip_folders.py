import all_loggers
import shutil


def zip_it(path):
    all_loggers.logger_log.info('Entered Into zip_it function. now zipping it.')
    x = shutil.make_archive(path, 'zip', path)
    all_loggers.logger_log.info(f"Zipping is done with Path {x}")
    return x

    # '''Old Code'''
    # def zipdir(path_, ziph):
    #     for root, dirs, files in os.walk(path_):
    #         for file_ in files:
    #             ziph.write(os.path.join(root, file_))
    # try:
    #     file = path + ".zip"
    #     zipf = zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED)
    #     zipdir(path, zipf)
    #     zipf.close()
    #     return file
    # except Exception as e:
    #     all_loggers.logger_log.exception(e)
    #     raise
