"""
        wb = xlrd.open_workbook(from_file)
        sheet = wb.sheet_by_name('Perf Test Case Final')
        sheet_dict = {}
        logging.info('Read Perf Test Case Final Sheet')
        for i in range(1, sheet.nrows):
            nl_txn_name = str(sheet.cell_value(i, 3)).strip()
            key_nl = format_nl_name(nl_txn_name)
            logging.info('{org_name} converted to {new_name}'.format(
                org_name=nl_txn_name, new_name=key_nl))
            if key_nl is None:
                continue

            json_dict = {
                'op_txn_name': str(sheet.cell_value(i, 2)).encode().decode('ascii', 'ignore'),
                'expected_response_time': float(sheet.cell_value(i, 4)).__round__(1),
                'scenario': str(sheet.cell_value(i, 0)).encode().decode('ascii', 'ignore'),
                'wpm': float(sheet.cell_value(i, 1)).__round__(2),
                'pacing': float(sheet.cell_value(i, 1)).__round__(2),
            }

            time.sleep(0.01)
            sheet_dict[key_nl] = json.dumps(json_dict)


"""

import json
import xml.etree.ElementTree as Et

import all_loggers


def format_nl_name(name):
    name = name if len(name) < 57 else name[0:12] + '...' + name[-40:]
    return name


ln = '\n'


def put_from_file(xml_element, sheet_dict):
    for k, v in sheet_dict.items():
        sheet_dict.update({k: json.dumps(v, indent=2)})
    try:
        txns = [
            txn for txn in xml_element.findall('basic-logical-action-container')
            if str(txn.attrib['name']).lower() not in ['login', 'logout']
        ]

        nl_project_txn_name_list = [
            format_nl_name(str(txn.attrib['name'])) for txn in txns
        ]

        all_loggers.logger_log.info(f'List of NL Project TXNs {ln} :{nl_project_txn_name_list}')

        for txn in txns:
            txn_name_org = txn.attrib['name']
            txn_name = format_nl_name(txn_name_org)
            if txn_name[0] == '#':
                all_loggers.logger_log.info(f"Skipped Txn {txn_name_org}:{txn_name} B'cause Starts with #")
                continue
            if txn_name in sheet_dict:
                if len(txn.findall('description')) == 0:
                    Et.SubElement(txn, 'description').text = sheet_dict[txn_name]
                else:
                    txn.findall('description')[0].text = sheet_dict[txn_name]
                all_loggers.logger_log.info(f'Successfully desc inserted for {txn_name}')
                del sheet_dict[txn_name]
                nl_project_txn_name_list.remove(txn_name)
            else:
                all_loggers.logger_log.info(f'NL TXN {txn_name} not in Excel')
        if len(sheet_dict) != 0:
            print(f"These not there in NL Project: {ln}{ln.join([keys for keys in sheet_dict])}")
            all_loggers.logger_log.info(f'''
            These TXNs from OP Do'nt Exist In NL Project
            By Passing It. 😃
            {ln.join([keys for keys in sheet_dict])}''')

        if len(nl_project_txn_name_list) != 0:
            print(f"These TXNs don't Exist the Sheet:{ln}{ln.join(nl_project_txn_name_list)}")
            all_loggers.logger_log.info(f'''
            Note: If you run the Perf TEST with this TXN, Reporting tool will Fail as there will be No JSON Desc
            TXNs from NL Do'nt Exist In Operational Profile
            By Passing It. 😃
            {ln.join(nl_project_txn_name_list)}
            ''')
            return nl_project_txn_name_list
        return 0

        # return xml_element

    except Exception as e:
        print(f'Exception Occurred in Put Description {e}')
        all_loggers.logger_log.exception(e)
