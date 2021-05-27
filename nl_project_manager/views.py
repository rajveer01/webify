from django.shortcuts import render
import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import cx_Oracle
import sqlite3
import json
from dotmap import DotMap


local_db_vars = DotMap()

with sqlite3.connect('helper.db') as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * From helper_variables')
    for row in cursor.fetchall():
        setattr(local_db_vars, row[0], row[1])
conn.close()

# Create your views here.


def home(request):
    with cx_Oracle.connect(local_db_vars.oracle_db_cs) as conn:
        with conn.cursor() as curs:
            sql_app_name = 'SELECT APP FROM  PLAB_SERVERS_T'
            curs.execute(sql_app_name)
            app_list = [li[0] for li in curs.fetchall()]
    context = {'app_list': app_list, 'run_tool': 'nl_project_manager'}
    print(app_list)

    return render(request, 'test_report_automation/index.html', context=context)


def print_me(request):
    x = request.GET['text']
    print(x)
    return HttpResponse(f'<h1> {x}</h1>')