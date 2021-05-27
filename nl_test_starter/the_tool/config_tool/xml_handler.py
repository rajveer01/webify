import lxml.etree as ET
import all_loggers


logging = all_loggers.logger_log


def xml_handler(file_data, xpath, data):

    if '<?xml version="1.0" encoding="UTF-8"?>' in file_data:
       file_data = file_data.split('<?xml version="1.0" encoding="UTF-8"?>', 1)[1]  #splitting XML into 2 parts

    root = ET.fromstring(file_data)


    prev_value = ''

    data_list = data.split('\n', 1)
    element = root.findall(xpath)[0]                                        #finding xpath

    # if data_list[0].lower() == 'tag':
    #     xml_to_add = ET.fromstring(data_list[1])
    #     prev_value = ET.tostring(element, encoding='utf8', method='xml')
    #     print(prev_value, 'from here')
    #     '''if xml to add in element'''
    #     if True:
    #         element.append(xml_to_add)
    # elif data_list[0].lower() == 'tag value':
    #     prev_value = str(element.text)
    #     element.text = data_list[1]
    if data_list[0].lower() == 'attribute':                                  #handling the values for Attributes from Data
        attrib_kv_pair = data_list[1].split('=')
        prev_value = str(element.attrib)
        element.attrib[attrib_kv_pair[0]] = attrib_kv_pair[1]
        logging.info(
            "Previous Value is :{},root value is :{}, new value is :{}".format(prev_value, ET.tostring(root).decode(), attrib_kv_pair[1]))

    # logging.info("Previous Value is :{},root value is :{}, new value is :{}".format())
    return prev_value, ET.tostring(root).decode(), ET.tostring(root.findall(xpath)[0]).decode()




