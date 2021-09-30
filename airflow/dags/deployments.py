import datetime
import textwrap
from typing import Sequence
import itertools
import logging
from typing import Mapping

import airflow.utils.dates
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.providers.google.suite.hooks.sheets import GSheetsHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import psycopg2.extras

LOGGER = logging.getLogger(__name__)

DESCRIPTION = """
Retrieve deployment data from Google drive and insert into database 
"""

DAG_KWARGS = dict(
    dag_id='deployments',
    # This isn't time-dependent
    start_date=airflow.utils.dates.days_ago(1),
    schedule_interval=datetime.timedelta(days=1),
    description=DESCRIPTION,
)


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


def insert_deployments(*args, task_instance, test_mode: bool = False,
                       **kwargs):
    # Get results of previous task
    rows = task_instance.xcom_pull('get_deployments')
    deployments = clean_rows(rows)

    # Connect to target database
    hook = PostgresHook('database')
    connection = hook.get_conn()
    with connection.cursor() as cursor:
        # Replace all values in deployment table
        sql = textwrap.dedent("""
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
            ,zone         
            ,description  
            ,height       
            ,comments     
            ,person       
            ,co2_baseline   
        )
        VALUES %s;
        """)
        LOGGER.info(sql)
        psycopg2.extras.execute_values(
            cur=cursor,
            sql=sql,
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
                    dep.get('zone'),
                    dep.get('description'),
                    dep.get('height'),
                    dep.get('comments'),
                    dep.get('person'),
                    dep.get('co2_baseline', 0)
                )
                for dep in deployments
            ),
            page_size=1000,
        )

    if test_mode:
        connection.rollback()
    else:
        connection.commit()


with airflow.DAG(**DAG_KWARGS) as dag:
    deployments_info = Variable.get('deployments', deserialize_json=True)
    get_deployments = PythonOperator(
        task_id='get_deployments',
        doc='Download Google Sheet deployment info',
        python_callable=get_deployments_values,
        execution_timeout=datetime.timedelta(minutes=1),
        op_kwargs=dict(
            # Arguments for GSheetsHook.get_values
            get_values_kwargs=dict(
                spreadsheet_id=deployments_info['sheet_id'],
                range_=deployments_info['tab'],
            )
        )
    )

    update_deployments = PythonOperator(
        task_id='update_deployments',
        doc='Insert deployment info into database',
        python_callable=insert_deployments,
        execution_timeout=datetime.timedelta(minutes=1),
    )

    get_deployments >> update_deployments
