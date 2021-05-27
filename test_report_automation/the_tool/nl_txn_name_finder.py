import all_loggers
import xml.etree.ElementTree as Et
import zipfile

import gps


def format_nl_name(name):
    name = ' '.join(name.split())
    name = name if len(name) < 57 else name[0:12] + '...' + name[-40:]
    return name


def get_dict():
    try:
        project_path = gps.execution_project_folder + r"\config.zip"
        all_loggers.logger_log.info('Entered the Get_dict() function for reading the config.zip file:{}'.format(project_path))
        with zipfile.ZipFile(project_path) as archive:
            repo_file = archive.read("repository.xml")
            archive.close()
        all_loggers.logger_log.info('Zip file reading completed.')
        tree = Et.ElementTree(Et.fromstring(repo_file))
        root = tree.getroot()
        txns = root.findall("basic-logical-action-container")
        # txn_description_dict = {txn.attrib["name"]: txn.find("description").text for txn in txns
        # if str(txn.attrib["name"]).upper() not in ["LOGIN", "LOGOUT", "DUMMY", "HEALTH"]}

        txn_description_dict = {}
        for txn in txns:
            if str(txn.attrib["name"]).upper() not in ["LOGIN", "LOGOUT", "DUMMY", "HEALTH"]:
                all_loggers.logger_log.info(f'Doing for : {txn.attrib["name"]}')
                txn_description_dict[txn.attrib["name"]] = txn.find("description").text

        txn_description_dict_fresh = {}
        for k in txn_description_dict:
            txn_description_dict_fresh[format_nl_name(k)] = txn_description_dict[k]
        all_loggers.logger_log.info('Found all_ txn names and their descriptions.')
        return txn_description_dict_fresh
    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
