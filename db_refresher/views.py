from django.shortcuts import render, redirect
from django.http import HttpResponse
import json
from datetime import datetime as dt
import os
import subprocess
import time


# Create your views here.
def home(request):
    if request.method == 'GET':  # THis Means Form Opening
        return render(request, 'db_refresher/db_refresher.html')
    elif request.method == 'POST':  # this means Form Submitting
        data = request.POST.copy()
        for key, value in data.items():
            data[key] = value.strip()
        db_hostname = request.POST.get('db_hostname', None)
        new_schema_name = request.POST.get('new_schema_name', None)
        data['emails'] = [li.strip() for li in str(data['emails']).split('\n')]
        ts = dt.now().strftime('%b %d, %Y %I.%M.%S %p ')

        tool_dir = 'db_refresher/the_tool'
        param_dir = f'{tool_dir}/param_files/'
        file_name = '_'.join([new_schema_name, db_hostname, ts, '.json'])

        if not os.path.exists(param_dir):
            os.makedirs(param_dir)

        with open(f'{param_dir}/{file_name}', 'w') as f:
            f.write(json.dumps(data, indent=4))

        log_folder = os.path.join(tool_dir, 'Run Logs')

        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        log_file_with_path = os.path.join(log_folder, file_name)
        std_out_file = log_file_with_path + '.stdout'
        std_err_file = log_file_with_path + '.stderr'
        with open(std_out_file, 'w') as fo:
            with open(std_err_file, 'w') as fe:
                subprocess.Popen(
                    ['python',
                     f'{tool_dir}/db_refresher.py',
                     f'param_files/{file_name}',  # param_files/New Schema Name_db_ip_Jan 20, 2020 10.06.59 PM _.json
                     f'{file_name}.log',   # New Schema Name_db_ip_Jan 20, 2020 10.06.59 PM _.json
                     'Run Logs',
                     f'{tool_dir}',  # tool Location
                     'import'
                     ],
                    stdout=fo,
                    stderr=fe)
        context = {
            'std_out_file': std_out_file,
            'std_err_file': std_err_file,
            'run_log_file': os.path.join(log_folder, f'{file_name}.log')
        }
        return render(request, 'main_page/run_tracker.html', context=context)

        # db_hostname = request.POST.get('db_hostname', None)
        # current_schema_name = request.POST.get('current_schema_name', None)
        # new_schema_name = request.POST.get('new_schema_name', None)
        # table_space_location = request.POST.get('table_space_location', None)
        # dump_file_name = request.POST.get('dump_file_name', None)
        # dump_file_directory = request.POST.get('dump_file_directory', None)
        # dump_schema_name = request.POST.get('dump_schema_name', None)
        # REMAP_TABLESPACE_DATA = request.POST.get('REMAP_TABLESPACE_DATA', None)
        # REMAP_TABLESPACE_IDX = request.POST.get('REMAP_TABLESPACE_IDX', None)
        # sid = request.POST.get('sid', None)
        # db_port = request.POST.get('db_port', None)
        # user = request.POST.get('user', None)
        # pwd = request.POST.get('pwd', None)
        # db_ssh_Port = request.POST.get('db_ssh_Port', None)
        # SystemUserPassword = request.POST.get('SystemUserPassword', None)
        # No_Of_DataFiles = request.POST.get('No_Of_DataFiles', None)
        # No_Of_IndexFiles = request.POST.get('No_Of_IndexFiles', None)
        # enterprise_name = request.POST.get('enterprise_name', None)
        # result_database_name = request.POST.get('result_database_name', None)

        pass


