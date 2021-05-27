import cx_Oracle
import PySimpleGUI as Sg
import paramiko
from paramiko import SSHClient
import zipfile
import io
from xlwt import Workbook
from datetime import datetime as dt

oracle_db_cs = 'MS_PLAB/MS_PLAB@msstore:1522/db11203'

with cx_Oracle.connect(oracle_db_cs) as conn:
    with conn.cursor() as cursor:
        sql_app_name = 'SELECT APP FROM PLAB_SERVERS_T'
        cursor.execute(sql_app_name)
        app_list = [li[0] for li in cursor.fetchall()]

        layout = [[Sg.Text('Select App Name', justification='left', size=(20, 1), click_submits=True),
                   Sg.InputOptionMenu(app_list, size=(20, 1), key='app_name', )]]

        window = Sg.Window('PLab Reporting Automation', layout)
        event, values = window.read()
        if event in (None, 'Cancel'):
            exit(0)
        app_name = values['app_name']
        window.close()
        query = '''SELECT APP_IP, DB_IP, SYSTEMI_PATH, DB_HOME, SCHEMA_NAME, SCHEMA_PWD, APP_ORACLE_PWD,
                APP_ROOT_PWD,DB_ORACLE_PWD, DB_ROOT_PWD, THREADDUMP_FILE_PATH, WINDOWS_IP FROM PLAB_SERVERS_T
                WHERE APP = :APP'''
        query_format = {'APP': app_name}
        cursor.execute(query, query_format)
        row = cursor.fetchone()

app_IP = row[0]
db_IP = row[1]
SystemI_Path = row[2]
db_home = row[3]
schema_name = row[4]
schema_pwd = row[5]
App_Oracle_PWD = row[6]
App_Root_PWD = row[7]
DB_Oracle_PWD = row[8]
DB_Root_PWD = row[9]
threaddump_file_path = row[10]
execution_IP = row[11]
user = "oracle"
pwd = "oracle"


