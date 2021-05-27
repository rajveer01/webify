import all_loggers
import xml.etree.ElementTree as Et

import gps


def get_table():
    try:
        all_loggers.logger_log.info('Entered into get table function.')

        with open('scripts/sql_no_compare.sql', 'r') as f:
            sql = f.read()

        with open('scripts/sql_with_compare.sql', 'r') as f:
            sql_compare = f.read()

        """ Old SQL 
                sql = '''
                WITH ct1 AS(
                SELECT SCENARIO_NAME,TEST_RUN_NO, ROW_ID, OP_TRANSACTION_NAME,
                EXPECTED_RESPONSE_TIME,RESULT_90_PERC,EXPECTED_WPM,
                RESULT_COUNT,RESULT_ERROR_PERC, TEST_TYPE
                FROM PT_RESULTS WHERE RELEASE_NAME = :RELEASE_NAME AND APP_NAME = :APP_NAME AND 
                TEST_RUN_NO = :TEST_RUN_NO AND TEST_TYPE = :TEST_TYPE ORDER BY ROW_ID),
                ct2 as (SELECT SCENARIO_NAME, MIN(RESULT_COUNT) as ACHIEVED_WPM, 
                COUNT(SCENARIO_NAME) AS OCCURRENCE FROM (SELECT SCENARIO_NAME,RESULT_COUNT FROM PT_RESULTS
                WHERE RELEASE_NAME = :RELEASE_NAME AND APP_NAME = :APP_NAME AND TEST_RUN_NO = :TEST_RUN_NO AND 
                TEST_TYPE = :TEST_TYPE ORDER BY ROW_ID) GROUP BY SCENARIO_NAME)
                SELECT ct1.SCENARIO_NAME, ct1.OP_TRANSACTION_NAME, ct1.EXPECTED_RESPONSE_TIME, ct1.RESULT_90_PERC, 
                ct1.EXPECTED_WPM, ct2.ACHIEVED_WPM , ct1.RESULT_ERROR_PERC, ct2.OCCURRENCE FROM ct1 LEFT OUTER JOIN ct2 
                ON ct1.SCENARIO_NAME = ct2.SCENARIO_NAME ORDER BY ct1.ROW_ID
                '''
        
                sql_compare = '''
                WITH ct1 AS
                (SELECT SCENARIO_NAME, ROW_ID, OP_TRANSACTION_NAME, NL_TRANSACTION_NAME, EXPECTED_RESPONSE_TIME, 
                RESULT_90_PERC,
                EXPECTED_WPM, RESULT_COUNT, RESULT_ERROR_PERC FROM PT_RESULTS WHERE RELEASE_NAME = :RELEASE_NAME AND 
                APP_NAME = :APP_NAME AND TEST_RUN_NO = :TEST_RUN_NO AND TEST_TYPE = :TEST_TYPE), 
                ct2 AS (SELECT NL_TRANSACTION_NAME, RESULT_90_PERC FROM PT_RESULTS WHERE 
                RELEASE_NAME = :old_RELEASE_NAME AND APP_NAME = :APP_NAME AND 
                TEST_RUN_NO = :old_TEST_RUN_NO AND TEST_TYPE=:old_TEST_TYPE),
                ct3 AS (select SCENARIO_NAME, MIN(RESULT_COUNT) as ACHIEVED_WPM, COUNT(SCENARIO_NAME) AS OCCURRENCE FROM 
                (SELECT SCENARIO_NAME, RESULT_COUNT FROM PT_RESULTS
                WHERE RELEASE_NAME = :RELEASE_NAME AND APP_NAME = :APP_NAME AND TEST_RUN_NO = :TEST_RUN_NO AND 
                TEST_TYPE = :TEST_TYPE ORDER BY ROW_ID) GROUP BY SCENARIO_NAME)
                SELECT ct1.SCENARIO_NAME, ct1.OP_TRANSACTION_NAME, ct1.EXPECTED_RESPONSE_TIME, ct1.RESULT_90_PERC, 
                ct1.EXPECTED_WPM, ct3.ACHIEVED_WPM, ct1.RESULT_ERROR_PERC, ct3.OCCURRENCE, ct2.RESULT_90_PERC AS 
                old_RESULT_90_PERC
                FROM ct1 LEFT OUTER JOIN ct2 ON ct1.NL_TRANSACTION_NAME = ct2.NL_TRANSACTION_NAME LEFT OUTER JOIN ct3 ON 
                ct1.SCENARIO_NAME = ct3.SCENARIO_NAME ORDER BY ct1.ROW_ID
                '''
        """

        sql_format = {
            'RELEASE_NAME': gps.release_name, 'APP_NAME': gps.app_name, 'TEST_RUN_NO': gps.run,
            'TEST_TYPE': gps.test_type
        }

        sql_format_compare = {
            'RELEASE_NAME': gps.release_name, 'APP_NAME': gps.app_name, 'TEST_RUN_NO': gps.run,
            'old_RELEASE_NAME': gps.old_release_name, 'old_TEST_RUN_NO': gps.old_run,
            'TEST_TYPE': gps.test_type,
            'old_TEST_TYPE': gps.old_test_type
        }

        if gps.compare_with_old:
            all_loggers.logger_log.info(f'''Executing the select query for SQL compare with {sql_compare}
            {sql_format_compare}''')
            gps.global_cursor.execute(sql_compare, sql_format_compare)
        else:
            all_loggers.logger_log.info(f'''Executing the select query for SQL no-compare with {sql} \n {sql_format}''')
            gps.global_cursor.execute(sql, sql_format)

        txns = gps.global_cursor.fetchall()

        old_test_description = ''
        old_test_start_time = ''
        if gps.compare_with_old:
            all_loggers.logger_log.info(
                '''Calculating the OLD Run Description'''
            )
            query_for_description = '''
            SELECT DISTINCT TEST_START_DATE, TEST_DESCRIPTION FROM PT_RESULTS 
            WHERE APP_NAME = :APP_NAME AND RELEASE_NAME = :RELEASE_NAME AND 
            :TEST_RUN_NO = TEST_RUN_NO'''

            query_for_description_format = {
                'APP_NAME': gps.app_name,
                'RELEASE_NAME': gps.old_release_name,
                'TEST_RUN_NO': gps.old_run
            }
            all_loggers.logger_log.info(f'''Running query: {query_for_description} 
            Execution For Old Run Description with {query_for_description_format}''')

            gps.global_cursor.execute(query_for_description, query_for_description_format)

            old_run_details = gps.global_cursor.fetchone()
            old_test_start_time = old_run_details[0]
            old_test_start_time = old_test_start_time.strftime('%b %d, %Y ')
            old_test_description = old_run_details[1]

            all_loggers.logger_log.info(f'Old Run Description As {old_test_start_time} and {old_test_description}')

        shell_header = 'background-color: rgb(91, 155, 213); color: white; font-weight: bold;'
        shell_red = 'background-color: rgb(220, 50, 50); color:white; font-weight: bold;'
        shell_yellow = 'background-color: yellow; font-weight: bold;'
        shell_bg = {True: ' background-color: rgb(221, 235, 247);', False: ' background-color: rgb(255, 255, 252);'}
        snc_name_for_color = ""
        shell_bg_color_selected = True
        snc_name_for_merge = ""
        var_old_result_90_perc = 0
        # shell_show_display_selected = True
        all_loggers.logger_log.info('Constructing the table now.')
        table = Et.Element('table', border='2px')

        th = Et.SubElement(table, "tr", style=shell_header)
        Et.SubElement(th, 'th').text = 'S. NO'                      # 'TXN_NUMBER'
        Et.SubElement(th, 'th').text = 'Scenario Name'              # 'SCENARIO_NAME'
        Et.SubElement(th, 'th').text = 'Expected WPH'               # 'EXPECTED_WPM'
        Et.SubElement(th, 'th').text = 'Achieved WPH'               # 'RESULT_COUNT'
        Et.SubElement(th, 'th').text = 'Transaction Name'           # 'OP_TRANSACTION_NAME'
        Et.SubElement(th, 'th').text = 'Expected SLA RT (Sec)'      # 'EXPECTED_RESPONSE_TIME'
        Et.SubElement(th, 'th').text = f'''Current Test - Run: #{gps.run} 
        - {gps.run_description} - {gps.test_start_time.strftime('%b %d, %Y ')} - RT Sec'''  # 'RESULT_90_PERC'

        if gps.compare_with_old:                                    # 'old_RESULT_90_PERC'
            Et.SubElement(th, 'th').text = f'''Previous Test - Run: #{gps.old_run} 
            - {old_test_description} - {old_test_start_time} - RT Sec'''

        Et.SubElement(th, 'th').text = 'Error Percentage'              # 'RESULT_ERROR_PERC'

        txn_count = 0
        scn_count = 0
        failed_txns = 0
        yellow_txns = 0
        error_in_txns = 0
        less_wpm_scenarios = 0
        wpm_expected_dict = {}
        wpm_achieved_dict = {}

        for txn in txns:
            txn_count += 1

            # SCENARIO_NAME, OP_TRANSACTION_NAME,EXPECTED_RESPONSE_TIME,RESULT_90_PERC,
            #       0              1                  2                      3
            # EXPECTED_WPM, ACHIEVED_WPM, RESULT_ERROR_PERC, OCCURRENCE, old_RESULT_90_PERC
            #       4              5              6               7               8

            var_scenario_name = txn[0]
            var_op_transaction_nam = txn[1]
            var_expected_response_time = float(txn[2])
            var_result_90_perc = 0 if txn[3] is None else float(txn[3])
            var_expected_wpm = float(txn[4]) if gps.is_float(str(txn[4])) else -1
            var_result_count = float(txn[5]) if gps.is_float(str(txn[5])) else -1
            var_result_error_perc = float(txn[6]) if gps.is_float(str(txn[6])) else 0
            var_no_of_txns = str(txn[7])
            if gps.compare_with_old:
                var_old_result_90_perc = 0 if txn[8] is None else float(txn[8])

            if var_expected_wpm != -1:
                wpm_expected_dict[var_scenario_name] = var_expected_wpm

            if var_scenario_name in wpm_achieved_dict:
                if var_result_count < wpm_achieved_dict[var_scenario_name] and var_result_count != -1:
                    wpm_achieved_dict[var_scenario_name] = var_result_count
            else:
                wpm_achieved_dict[var_scenario_name] = var_result_count

            tr = Et.SubElement(table, "tr")

            if snc_name_for_color == var_scenario_name:
                pass
            else:
                snc_name_for_color = var_scenario_name
                shell_bg_color_selected = not shell_bg_color_selected

            if snc_name_for_merge == var_scenario_name:
                shell_show_display_selected = False
            else:
                shell_show_display_selected = True
                snc_name_for_merge = var_scenario_name

            Et.SubElement(tr, 'td', style=shell_bg[shell_bg_color_selected]).text = str(txn_count)      # 'TXN_NUMBER'
            if shell_show_display_selected:
                Et.SubElement(tr, 'td', rowspan=var_no_of_txns,
                              style=shell_bg[shell_bg_color_selected]).text = str(var_scenario_name)   # 'SCENARIO_NAME'
                scn_count += 1
            if shell_show_display_selected:
                Et.SubElement(tr, 'td', rowspan=var_no_of_txns,
                              style=shell_bg[shell_bg_color_selected]).text = str(var_expected_wpm)     # 'EXPECTED_WPM'
            if shell_show_display_selected:
                if var_expected_wpm > var_result_count and gps.wpm_matters:
                    Et.SubElement(tr, 'td', rowspan=var_no_of_txns,
                                  style=shell_red).text = str(var_result_count)                         # 'RESULT_COUNT'
                    less_wpm_scenarios += 1
                else:
                    Et.SubElement(tr, 'td', rowspan=var_no_of_txns,
                                  style=shell_bg[shell_bg_color_selected]).text = str(var_result_count)  # RESULT_COUNT'
                    less_wpm_scenarios += 0
            Et.SubElement(tr, 'td', style=shell_bg[shell_bg_color_selected]).text = str(var_op_transaction_nam)
            #                                                                                    # 'OP_TRANSACTION_NAME'
            Et.SubElement(tr, 'td', style=shell_bg[shell_bg_color_selected]).text = str(var_expected_response_time)
            #                                                                                 # 'EXPECTED_RESPONSE_TIME'
# -------------------------------p1s-------------------------------
            if var_expected_response_time < var_result_90_perc:                                # 'RESULT_90_PERC'
                Et.SubElement(tr, 'td', style=shell_red).text = str(var_result_90_perc)
                failed_txns += 1
            elif (var_expected_response_time * 0.90) < var_result_90_perc:
                Et.SubElement(tr, 'td', style=shell_yellow).text = str(var_result_90_perc)
                yellow_txns += 1
            else:
                Et.SubElement(tr, 'td', style=shell_bg[shell_bg_color_selected]).text = str(var_result_90_perc)

# -------------------------------p1e-------------------------------
# -------------------------------p2s-------------------------------
            if gps.compare_with_old:
                if var_expected_response_time < var_old_result_90_perc:                         # old_RESULT_90_PERC'
                    Et.SubElement(tr, 'td', style=shell_red).text = str(var_old_result_90_perc)
                elif (var_expected_response_time * 0.90) < var_old_result_90_perc:
                    Et.SubElement(tr, 'td', style=shell_yellow).text = str(var_old_result_90_perc)
                else:
                    if var_old_result_90_perc == 0:
                        Et.SubElement(tr, 'td', style=shell_bg[shell_bg_color_selected]).text = '-'
                    else:
                        Et.SubElement(tr, 'td',
                                      style=shell_bg[shell_bg_color_selected]).text = str(var_old_result_90_perc)
# -------------------------------p2e-------------------------------

            if var_result_error_perc < 10:                                                      # 'RESULT_ERROR_PERC'
                Et.SubElement(tr, 'td', style=shell_bg[shell_bg_color_selected]).text = str(var_result_error_perc)
            else:
                Et.SubElement(tr, 'td', style=shell_red).text = str(var_result_error_perc)      # 'RESULT_ERROR_PERC'
                error_in_txns += 1
            all_loggers.logger_log.info('Constructed the row {}'.format(Et.tostring(tr).decode()))

        total_expected_wpm = 0
        for key in wpm_expected_dict:
            total_expected_wpm += float(wpm_expected_dict[key]) if gps.is_float(str(wpm_expected_dict[key])) else 0
        total_expected_wpm = (total_expected_wpm / 60).__round__(2)

        total_achieved_wpm = 0
        for key in wpm_expected_dict:
            total_achieved_wpm += float(wpm_achieved_dict[key])if gps.is_float(str(wpm_achieved_dict[key])) else 0
        test_duration = round((gps.test_stop_time - gps.test_start_time).seconds / 60, 2)
        total_achieved_wpm = round(total_achieved_wpm / test_duration, 2)

        gps.wpm_required = total_expected_wpm
        gps.wpm_achieve = total_achieved_wpm

        return {'table': table, 'txn_count': txn_count, 'failed_txns': failed_txns, 'yellow_txns': yellow_txns,
                'scn_count': scn_count, 'total_expected_wpm': total_expected_wpm,
                'total_achieved_wpm': total_achieved_wpm, 'error_in_txns': error_in_txns,
                'less_wpm_scenarios': less_wpm_scenarios}

    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
