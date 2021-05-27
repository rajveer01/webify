from django.shortcuts import render
from django.http import HttpResponse
from dotmap import DotMap
import cx_Oracle
import sqlite3
import json

local_db_vars = DotMap()

with sqlite3.connect('helper.db') as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * From helper_variables')
    for row in cursor.fetchall():
        setattr(local_db_vars, row[0], row[1])
conn.close()


def home(request):
    with cx_Oracle.connect(local_db_vars.oracle_db_cs) as conn:
        with conn.cursor() as curs:
            sql_app_name = 'SELECT APP FROM  PLAB_SERVERS_T'
            curs.execute(sql_app_name)
            app_list = [li[0] for li in curs.fetchall()]
    context = {'app_list': app_list, 'run_tool': 'test_report_automation'}
    return render(request, 'test_report_automation/index.html', context=context)


def apps_name(request):  # Ajax
    with cx_Oracle.connect(local_db_vars.oracle_db_cs) as conn:
        with conn.cursor() as curs:
            sql_app_name = 'SELECT APP FROM  PLAB_SERVERS_T'
            curs.execute(sql_app_name)
            app_list = [li[0] for li in curs.fetchall()]
    return HttpResponse(json.dumps(app_list))


def base(request):
    return render(request, 'test_report_automation/base.html')


def max_run(request):  # Ajax

    release_name = request.POST.get('release_name')
    test_type = request.POST.get('test_type')
    app = request.POST.get('app_name')

    print(release_name, app, test_type)

    with cx_Oracle.connect(local_db_vars.oracle_db_cs) as conn:
        with conn.cursor() as curs:

            query_run = '''
                            SELECT COALESCE(MAX(Test_Run_No), 0) FROM PT_RESULTS WHERE 
                            RELEASE_NAME = :Release_Name and APP_NAME = :App_Name and TEST_TYPE = :Test_type
                            '''
            query_run_format = {'Release_Name': release_name, 'App_Name': app, 'Test_type': test_type}

            print(query_run_format)
            curs.execute(query_run, query_run_format)
            run_no = curs.fetchone()[0]
            print(run_no)
            run_no = int(run_no) + 1
            test_run_no = run_no.__str__()
            response = {
                'TEST_RUN_NO': test_run_no,
            }

            return HttpResponse(json.dumps(response))


def max_run_old(request):  # Ajax
    old_release_name = request.POST.get('release_name')
    old_test_type = request.POST.get('test_type')
    app = request.POST.get('app_name')

    with cx_Oracle.connect(local_db_vars.oracle_db_cs) as conn:
        with conn.cursor() as curs:

            query_old_run = '''
            SELECT COALESCE(MAX(Test_Run_No), 0) As Run_Number FROM PT_RESULTS WHERE RELEASE_NAME = :Release_Name 
            and APP_NAME = :App_Name and TEST_TYPE = :old_test_type
            '''
            query_run_format = {'Release_Name': old_release_name, 'App_Name': app, 'old_test_type': old_test_type}

            curs.execute(query_old_run, query_run_format)
            old_run_no = curs.fetchone()[0]
            old_run_no = int(old_run_no)
            old_run = old_run_no.__str__()
            response = {
                'TEST_RUN_NO': old_run,
            }
            return HttpResponse(json.dumps(response))


