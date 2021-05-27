import PySimpleGUI as Sg
import cx_Oracle
import os


def paint_ui():
    try:
        params = {}
        with open("Clients/parameters.txt", "r") as f:
            for a in f.readlines():
                temp = a.split(':', 1)
                params[temp[0].strip()] = [temp[1].strip(), 'parameters.txt']
        with open("Clients/old_test_parameters.txt", "r") as f:
            for a in f.readlines():
                temp = a.split(':', 1)
                params[temp[0].strip()] = [temp[1].strip(), 'old_test_parameters.txt']
        with open("Clients/changes_made.txt", "r") as f:
            params['changes_made'] = [f.read(), 'changes_made.txt']
        with open("Clients/installers_to_avoid.txt", "r") as f:
            params['installers_to_avoid'] = [f.read(), 'installers_to_avoid.txt']
        with open("Clients/test_scope.txt", "r") as f:
            params['test_scope'] = [f.read(), 'test_scope.txt']
        with open("Clients/to_mail_file.txt", "r") as f:
            params['to_mail_file'] = [f.read(), 'to_mail_file.txt']

        app_name = params["app_name"][0]
        release_name = params["release_name"][0]
        svn_client = params["svn_client"][0]
        oracle_client_Path = params["oracle_client_Path"][0]
        oracle_db_cs = params["oracle_db_cs"][0]
        test_type = params["test_type"][0]
        old_test_type = params["old_test_type"][0]
        old_release_name = params["old_release_name"][0]

        os.environ['Path'] = oracle_client_Path + ';' + svn_client

        with cx_Oracle.connect(oracle_db_cs) as conn:
            with conn.cursor() as cursor:
                sql_app_name = 'SELECT APP FROM PLAB_SERVERS_T'
                sql_release_name = '''SELECT RELEASE_NAME FROM (SELECT RELEASE_NAME FROM PT_RESULTS GROUP BY 
                RELEASE_NAME ORDER BY MAX(ROW_ID) DESC) WHERE ROWNUM < 6'''
                cursor.execute(sql_app_name)
                app_list = [li[0] for li in cursor.fetchall()]
                app_name in app_list and app_list.remove(app_name)
                app_list.insert(0, app_name)

                cursor.execute(sql_release_name)
                release_list = [li[0] for li in cursor.fetchall()]
                release_name in release_list and release_list.remove(release_name)
                release_list.insert(0, release_name)

                test_type_list = ['Load Run', 'Dry Run']
                test_type in test_type_list and test_type_list.remove(test_type)
                test_type_list.insert(0, test_type)

                old_test_type_list = test_type_list.copy()
                old_test_type_list.insert(0, 'NA')
                old_test_type in old_test_type_list and old_test_type_list.remove(old_test_type)
                old_test_type_list.insert(0, old_test_type)

                old_release_list = release_list.copy()
                old_release_list.insert(0, 'NA')
                old_release_name in old_release_list and old_release_list.remove(old_release_name)
                old_release_list.insert(0, old_release_name)

        layout = [
            [Sg.Text('Select Test Type', justification='left', size=(20, 1)),
             Sg.InputOptionMenu(test_type_list, size=(20, 1), key='test_type')],

            [Sg.Text('Select Release Name', justification='left', size=(20, 1)),
             Sg.InputCombo(release_list, size=(20, 1), key='release_name')],

            [Sg.Text('Select App Name', justification='left', size=(20, 1)),
             Sg.InputOptionMenu(app_list, size=(20, 1), key='app_name')],

            [Sg.Text(50*'--' + 'For Result Comparision' + 50*'--', justification='left', size=(20, 1))],

            [Sg.Text('Select Old Test Type', justification='left', size=(20, 1)),
             Sg.InputOptionMenu(old_test_type_list, size=(20, 1), key='old_test_type')],

            [Sg.Text('Select Release Name', justification='left', size=(20, 1)),
             Sg.InputOptionMenu(old_release_list, size=(20, 1), key='old_release_name')],

            [Sg.Text('', size=(20, 1)), Sg.Button('Submit'), Sg.Button('Cancel')]
        ]

        window = Sg.Window('PLab Reporting Automation', layout)
        event, values = window.Read()
        if event in (None, 'Cancel'):
            exit(0)
        window.Close()

        params['app_name'][0] = values['app_name']
        params['release_name'][0] = values['release_name']
        params['test_type'][0] = values['test_type']
        params['old_test_type'][0] = values['old_test_type']
        params['old_release_name'][0] = values['old_release_name']

        params['app_name'][0] in app_list and app_list.remove(params['app_name'][0])
        app_list.insert(0, params['app_name'][0])

        params['release_name'][0] in release_list and release_list.remove(params['release_name'][0])
        release_list.insert(0, params['release_name'][0])

        params['old_test_type'][0] in old_test_type_list and old_test_type_list.remove(params['old_test_type'][0])
        old_test_type_list.insert(0, params['old_test_type'][0])

        params['old_release_name'][0] in old_release_list and old_release_list.remove(params['old_release_name'][0])
        old_release_list.insert(0, params['old_release_name'][0])

        with cx_Oracle.connect(oracle_db_cs) as conn:
            with conn.cursor() as cursor:
                query_run = '''
                SELECT COALESCE(MAX(Test_Run_No), 0) FROM PT_RESULTS WHERE 
                RELEASE_NAME = :Release_Name and APP_NAME = :App_Name and TEST_TYPE = :Test_type
                '''
                query_run_format = {'Release_Name': params['release_name'][0], 'App_Name': params['app_name'][0],
                                    'Test_type': params['test_type'][0]}
                cursor.execute(query_run, query_run_format)
                run_no = cursor.fetchone()[0]
                run_no = 0 if run_no is None else run_no
                run_no = int(run_no) + 1
                params['run'][0] = run_no.__str__()

                query_script_version = '''
                SELECT MAX(SCRIPT_VERSION) FROM PT_RESULTS WHERE RELEASE_NAME = :Release_Name and APP_NAME = :App_Name
                '''
                query_run_format = {'Release_Name': params['release_name'][0], 'App_Name': params['app_name'][0]}
                cursor.execute(query_script_version, query_run_format)

                script_version = cursor.fetchone()[0]
                script_version = 1 if script_version is None else script_version
                script_version = int(script_version)
                params['script_version'][0] = script_version.__str__()

                query_old_run = '''
                                SELECT COALESCE(MAX(Test_Run_No), 0) As Run_Number FROM PT_RESULTS WHERE RELEASE_NAME = :Release_Name 
                                and APP_NAME = :App_Name and TEST_TYPE = :old_test_type
                                '''
                query_run_format = {'Release_Name': params['old_release_name'][0], 'App_Name': params['app_name'][0],
                                    'old_test_type': params['old_test_type'][0]}
                cursor.execute(query_old_run, query_run_format)
                old_run_no = cursor.fetchone()[0]
                old_run_no = 0 if old_run_no is None else old_run_no
                old_run_no = int(old_run_no)
                params['old_run'][0] = old_run_no.__str__()

        def paint_ui():

            parameter_layout = [
                [Sg.Text('Release:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputOptionMenu(release_list, size=(20, 1), key='release_name', disabled=True),
                 Sg.Text('           App:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputOptionMenu(tuple(app_list), size=(15, 1), key='app_name', disabled=True)],

                [Sg.Text('Monitor Information:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputCombo(('MSI-MTD026', 'MSI-MTD040', 'MSI-AIO145', 'MSI-AIO176', 'NA'), size=(22, 1),
                               default_value=params['monitor_IP'][0], key='monitor_IP'),
                 Sg.Text('           Test Type:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputOptionMenu(['Load Run', 'Dry Run'], default_value=params['test_type'][0],
                                    size=(15, 1), key='test_type', disabled=True)],

                [Sg.Text('Run Description: ', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.Multiline(default_text=params['run_description'][0], key='run_description')],

                [Sg.Text('Total Users:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['total_users'][0], key='total_users')
                 ],

                [Sg.Text('NL Project Folder:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['execution_project_folder'][0], key='execution_project_folder'), Sg.FolderBrowse()],

                [Sg.Text('Test Artifact Folder:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['artifacts_folder'][0], key='artifacts_folder'), Sg.FolderBrowse()],

                [Sg.Text('Thread Dump Dir:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['thread_dump_location'][0], key='thread_dump_location')],

                [Sg.Text('Heap Dump Dir:', size=(15, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['heap_dump_location'][0], key='heap_dump_location')],

                [Sg.Checkbox(text='WPM Matters ?', default=params['wpm_matters'][0].upper() in ['TRUE'],
                             key='wpm_matters', visible=False)]
            ]

            result_additional_info = [
                [Sg.Text('Change History Link: ', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.Multiline(default_text=params['change_history'][0], key='change_history')],

                [Sg.Text('Test Scope: ', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.Multiline(default_text=params['test_scope'][0], key='test_scope')],

                [Sg.Text('Changes Made: ', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.Multiline(default_text=params['changes_made'][0], key='changes_made')]
            ]

            svn_layout = [
                [Sg.Text(' ')],
                [Sg.Text('SVN User Name:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['svn_user_name'][0], key='svn_user_name')],

                [Sg.Text('SVN Password:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['svn_password'][0], password_char='*', key='svn_password')],

                [Sg.Text('SVN Artifact Folder:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['svn_artifact_folder'][0], key='svn_artifact_folder')],


                [Sg.Text('SVN Operational Profile:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['svn_op_location'][0], key='svn_op_location')],

                [Sg.Text('SVN Client:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['svn_client'][0], key='svn_client')]
            ]

            oracle_layout = [
                [Sg.Text('')],

                [Sg.Text('PLAB Specific', font="Helvetica", relief=Sg.RELIEF_RIDGE)],

                [Sg.Text('Oracle Client Path:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['oracle_client_Path'][0], key='oracle_client_Path')],

                [Sg.Text('DB Connection String:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['oracle_db_cs'][0], key='oracle_db_cs')],

                [Sg.Text('')],

                [Sg.Text('APP Specific', font="Helvetica", relief=Sg.RELIEF_RIDGE)],

                [Sg.Text('Oracle DB Port:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['oracle_db_port'][0], key='oracle_db_port')],

                [Sg.Text('Oracle DB ID:', size=(18, 1), auto_size_text=False, justification='left'),
                 Sg.InputText(params['oracle_db_id'][0], key='oracle_db_id')]
            ]

            mail_layout = [
                [Sg.Text('')],

                [Sg.Text('Comparision', font="Helvetica"),
                 Sg.Checkbox(text='(Check to compare with older result)',
                             default=params['compare_with_old'][0].upper() in ['TRUE'], key='compare_with_old')],

                [Sg.Text('Select Old Release Name', justification='left', size=(20, 1)),
                 Sg.InputOptionMenu(old_release_list, size=(20, 1), key='old_release_name', disabled=False),
                 Sg.Text('Old Run #: ', size=(18, 1), auto_size_text=False, justification='right'),
                 Sg.Spin(values=tuple(range(0, int(params['old_run'][0])+1)), initial_value=int(params['old_run'][0]),
                         key='old_run')],

                [Sg.Text('Select Old Test Type', justification='left', size=(20, 1)),
                 Sg.InputOptionMenu(old_test_type_list, size=(20, 1), key='old_test_type', disabled=False)],

                [Sg.Text('Mail Recipients:'), Sg.Multiline(default_text=params['to_mail_file'][0], key='to_mail_file')],

                [Sg.Text('')]
            ]

            layout = [
                [Sg.Text(str('DevSena : Run - %s' % params['run'][0]).center(75), size=(34, 1), justification='center',
                         font=("Helvetica", 25), relief=Sg.RELIEF_RIDGE)],
                [Sg.Text(2*'---------------------------------------------------------------')],
                [
                    Sg.TabGroup(
                        [
                            [
                                Sg.Tab('Parameters', parameter_layout),
                                Sg.Tab('Test Info', result_additional_info),
                                Sg.Tab('SVN', svn_layout),
                                Sg.Tab('Oracle', oracle_layout),
                                Sg.Tab('Mail', mail_layout)
                            ]

                        ])
                ],
                [Sg.Text('', size=(25, 1)), Sg.Submit(), Sg.Cancel()]]

            window = Sg.Window('PLAB').Layout(layout)

            button, values = window.Read()
            window.Close()
            if button in (None, 'Cancel'):
                exit(0)

            del values['Browse']
            del values['Browse0']
            values['wpm_matters'] = 'True' if values['test_type'] == 'Load Run' else 'False'
            values['compare_with_old'] = str(values['compare_with_old'])
            values['old_run'] = str(values['old_run'])
            return values

        new_params = paint_ui()

        for key in new_params:
            params[key][0] = new_params[key].strip()

    except Exception as e:
        print(e)
        print()
        raise e

    else:
        cleared = []
        for key in params:
            file_mode = 'w' if params[key][1] not in cleared and (cleared.append(params[key][1]) or True) else 'a'
            with open("Clients/{}".format(params[key][1]), file_mode) as f:
                if params[key][1] in ['parameters.txt', 'old_test_parameters.txt']:
                    f.write(key + ':' + params[key][0] + '\n')
                else:
                    f.write(params[key][0] + '\n')


paint_ui()
