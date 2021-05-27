import json
import all_loggers
import time

import requests


def gen_report(project_ip, file_name, artifacts_folder):
    try:
        all_loggers.logger_log.info(
            'Entered into gen_report function for project IP: {}, file name {}, Folder {}'.format(project_ip, file_name,
                                                                                                  artifacts_folder))

        url_g = f"http://{project_ip}:7400/Results/v1/Service.svc/GenerateReport"
        url_d = f"http://{project_ip}:7400/Results/v1/Service.svc/DownloadReport"

        data = {"d": {"Format": "PDF", 'CustomReportContents': True, "FileName": file_name}}
        data = json.dumps(data)
        headers = {'Content-type': 'application/json'}
        resp = requests.post(url_g, data=data, headers=headers)

        count = 0
        while resp.status_code != 201:
            count += 1
            if count == 100:
                raise Exception(f'Status code{resp.status_code} not Zero for {project_ip}@{file_name} as {resp.text}')
            time.sleep(5)

        rep_id = (json.loads(resp.text))["d"]["ReportId"]

        all_loggers.logger_log.info(f'''Generate NL Report Executed with response code {resp.status_code} and 
        response {resp.text} and got 
        report id {rep_id}''')

        data = {"d": {"ReportId": rep_id}}
        data = json.dumps(data)

        resp = requests.post(url_d, data=data, headers=headers)
        while not str(resp.status_code) == '201':
            all_loggers.logger_log.info(f'''Wait for {project_ip} to generate the report, status: {resp.status_code}, 
            response:{resp.text}''')
            resp = requests.post(url_d, data=data, headers=headers)
            time.sleep(3)

        report_name = artifacts_folder + '/' + file_name
        open(report_name, 'wb').write(resp.content)
        all_loggers.logger_log.info(f'generated and save the report in {report_name}')

    except Exception as e:
        all_loggers.logger_log.exception(e)
        raise
