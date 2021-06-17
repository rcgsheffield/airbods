import datetime
from typing import Sequence
import itertools
import os
import logging
from typing import Mapping

import airflow.utils.dates
from airflow.operators.python import PythonOperator
from airflow.providers.google.suite.hooks.sheets import GSheetsHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg2.extras

LOGGER = logging.getLogger(__name__)


def clean_header(s: str) -> str:
    s = s.strip().casefold().replace(' ', '_')
    # Remove non-alphanumeric characters
    s = ''.join(c for c in s if c.isalnum() or c == '_')
    return s


def get_deployments_values(get_values_kwargs: Mapping, **kwargs) -> Sequence[
    list]:
    """
    Retrieve rows from spreadsheet
    """
    hook = GSheetsHook()

    return hook.get_values(**get_values_kwargs)


def convert_date(s: str) -> str:
    """
    Convert British date format to ISO 8601 date
    e.g. '16/04/2021' => '2021-04-16'
    """
    try:
        return datetime.datetime.strptime(s, '%d/%m/%Y').date().isoformat()
    # Ignore empty strings or nulls
    except (ValueError, TypeError):
        if s:
            raise


def clean_rows(rows) -> Sequence[dict]:
    """
    Build data rows with cleaned up column names
    """
    headers = [clean_header(s) for s in rows.pop(0)]
    return [dict(itertools.zip_longest(headers, row)) for row in rows]


def insert_deployments(*args, task_instance, **kwargs):
    # Get results of previous task
    rows = task_instance.xcom_pull('get_deployments')
    deployments = clean_rows(rows)

    # Connect to target database
    hook = PostgresHook('database')
    connection = hook.get_conn()
    with connection.cursor() as cursor:
        # Replace all values in deployment table
        psycopg2.extras.execute_values(
            cur=cursor,
            sql="""
            DELETE FROM airbods.public.deployment;
            INSERT INTO airbods.public.deployment (
                 serial_number
                ,start_time   
                ,end_time     
                ,verbose_name         
                ,city         
                ,site         
                ,area         
                ,floor        
                ,room         
                ,zone         
                ,description  
                ,height       
                ,comments     
                ,person          
            )
            VALUES %s;
            """,
            argslist=(
                (
                    dep['serial_number'],
                    convert_date(dep['start_date']),
                    convert_date(dep.get('end_date', '')),
                    dep['name'],
                    dep.get('city'),
                    dep.get('site'),
                    dep.get('area'),
                    dep.get('floor'),
                    dep.get('room'),
                    dep.get('zone'),
                    dep.get('description'),
                    dep.get('height'),
                    dep.get('comments'),
                    dep.get('person')
                )
                for dep in deployments
            ),
            page_size=1000,
        )

    connection.commit()


with airflow.DAG(
        dag_id='deployments',
        start_date=datetime.datetime(2021, 6, 16),
        schedule_interval=datetime.timedelta(days=1),
) as dag:
    get_deployments = PythonOperator(
        task_id='get_deployments',
        python_callable=get_deployments_values,
        op_kwargs=dict(
            # Arguments for GSheetsHook.get_values
            get_values_kwargs=dict(
                spreadsheet_id=os.environ['DEPLOYMENTS_SHEET_ID'],
                range_=os.environ['DEPLOYMENTS_TAB_NAME'],
            )
        )
    )

    update_deployments = PythonOperator(
        task_id='update_deployments',
        python_callable=insert_deployments,
    )

    # # Insert or update values
    # update_deployments = PostgresOperator(
    #     task_id='update_deployments',
    #     postgres_conn_id='database',
    #     sql=textwrap.dedent("""
    #     INSERT INTO airbods.public.deployment (
    #         serial_number
    #         ,start_time
    #         ,end_time
    #         ,verbose_name
    #         ,city
    #         ,site
    #         ,area
    #         ,floor
    #         ,room
    #         ,zone
    #         ,description
    #         ,height
    #         ,comments
    #         ,person
    #     VALUES
    #         {% for dep in task_instance.xcom_pull('get_deployments') %}
    #         {% if not loop.first %},{% endif %}
    #         ('{{ dep.serial_number }}', '{{ dep.start_date }}'::timestamptz,
    #         '{{ dep.end_date }}'::timestamptz, '{{ dep.name }}',
    #         '{{ dep.city }}', '{{ dep.site }}', '{{ dep.area }}',
    #         '{{ dep.floor }}', '{{ dep.room }}', '{{ dep.zone }}',
    #         '{{ dep.description }}', {{ dep.heightm|float }},
    #         '{{ dep.comments }}', '{{ dep.person }}')
    #         {% endfor %}
    #     ON CONFLICT (serial_number, start_time)
    #     DO UPDATE SET
    #          serial_number = EXCLUDED.serial_number
    #         ,start_time    = EXCLUDED.start_time
    #         ,end_time      = EXCLUDED.end_time
    #         ,verbose_name  = EXCLUDED.verbose_name
    #         ,city          = EXCLUDED.city
    #         ,site          = EXCLUDED.site
    #         ,area          = EXCLUDED.area
    #         ,floor         = EXCLUDED.floor
    #         ,room          = EXCLUDED.room
    #         ,zone          = EXCLUDED.zone
    #         ,description   = EXCLUDED.description
    #         ,height        = EXCLUDED.height
    #         ,comments      = EXCLUDED.comments
    #         ,person        = EXCLUDED.person
    #     """)
    # )

    get_deployments >> update_deployments
