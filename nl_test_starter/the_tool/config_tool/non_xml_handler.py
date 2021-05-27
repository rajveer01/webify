import math
import all_loggers


logging = all_loggers.logger_log


def non_xml_handler(file, ssh_app, bounds, expected, app_ram):
    try:
        delimiter = bounds
        value = expected
        prev_val = ''
        sftp_app = ssh_app
        sftp_app.get(file, file.split('/')[-1])

        if delimiter == 'At End':                                          # handling the httpd.conf file

            file_obj = open(file.split('/')[-1], 'r')
            file_data = file_obj.read()
            file_obj.seek(0)
            len_file = file_obj.readlines()
            # print(len(file_data))
            # print(len(len_file))
            file_obj.close()
            if len(len_file) < 700:  # to check for expected value is already present in file
                if value in file_data:                            # line numbers not proper parameter to consider
                    logging.info("We have NOT modified parameters of httpd.conf file")
                    return value, value
                total_file = file_data + '\n' + value
                # print(total_file)
                file_obj = open(file.split('/')[-1], 'w')
                total_file.replace('\r', '')
                file_obj.write(total_file)  # writing into the location
                file_obj.close()
                sftp_app.put(file.split('/')[-1], file)  # putting the modified file
                logging.info("We have modified parameters of httpd.conf file")
        else:
            file_obj = open(file.split('/')[-1], 'r')                          # Handling tomcat file
            file_data = file_obj.read()
            file_obj.close()
            delimiter_after, delimiter_before = delimiter.split('Before:', 1)   # Splitting for getting the bounds
            delimiter_after = delimiter_after.split('After:', 1)[1].strip()    # splitting for getting bounds
            delimiter_before = delimiter_before.strip()                        # splitting for getting bounds

            if delimiter_after == 'TOMCAT_XMX=':                                  # For Setting "TOMCAT_XMX" value
                # value = str(math.floor(int(app_ram) * .75)) + 'G\n'
                value = f'{math.floor((int(app_ram) - 4) * .857)}G\n'

                left = file_data.split(delimiter_after, 1)[0] + delimiter_after    # getting left_side part of delimiter
                right = delimiter_before + file_data.split(delimiter_before, 1)[1]  # getting right_side part of delimiter
                prev_val = file_data.split(delimiter_after, 1)[1].split(right)[0]   # for getting previous value

                total_file = left + value + '\n' + right                             # for constructing total file
                file_obj = open(file.split('/')[-1], 'wb')                           # opening the file in binary format
                total_file = total_file.replace('\r', '').encode()                   # replacing it with encoded file
                # print(total_file)
                file_obj.write(total_file)
                file_obj.close()
                sftp_app.put(file.split('/')[-1], file)                              # putting in to required location
                logging.info(f"Added the Value :{value}")

            else:
                left_bound = delimiter_after                                         # for getting left_bound
                right_bound = delimiter_before                                       # for getting right_bound
                a, b = file_data.split(left_bound, 1)
                b1, b2 = b.split(right_bound, 1)
                prev_val = b1
                new_val = a + left_bound + value + '\n' + right_bound + b2
                file_obj = open(file.split('/')[-1], 'wb')
                total_file = new_val.replace('\r', '').encode()
                file_obj.write(total_file)
                file_obj.close()
                sftp_app.put(file.split('/')[-1], file)
                logging.info(f"Added the Value :{value}")

        return prev_val, value
    except Exception as e:
        return f'Failed Due to {e}', 'NA'
