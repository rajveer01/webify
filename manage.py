#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import sqlite3
from dotmap import DotMap


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webify.settings')

    local_db_vars = DotMap()

    with sqlite3.connect('helper.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * From helper_variables')
        for row in cursor.fetchall():
            setattr(local_db_vars, row[0], row[1])
    conn.close()

    os.environ['PATH'] = os.environ['PATH'] + ';' + local_db_vars.oracle_client_Path + ';' + local_db_vars.svn_client

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
