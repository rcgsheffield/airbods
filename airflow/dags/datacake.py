import datetime
import pathlib
import textwrap
import json
import logging
from typing import Iterable

import airflow.models
import psycopg2.extras

from operators.graphql import GraphQLHttpOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models.taskinstance import TaskInstance

LOGGER = logging.getLogger(__name__)

DESCRIPTION = """
This workflow retrieves, stores and transforms the sensor data that is
downloaded from Datacake.
"""


def flatten_history(devices: Iterable[dict]) -> Iterable[dict]:
    """
    Process device historical data into rows
    """
    row_count = 0
    for device in devices:
        for row in json.loads(device.pop('history')):
            row_count += 1
            yield dict(**device, **row)

    LOGGER.info('Generated %s rows', row_count)


def bulk_load_values(*args, task_instance: TaskInstance, execution_date,
                     next_execution_date, test_mode: bool = False, **kwargs):
    # Get result of previous task
    raw_data = task_instance.xcom_pull('all_devices_history')
    # Parse JSON data
    devices = json.loads(raw_data)['data']['allDevices']

    # Convert GraphQL response to data rows
    rows = flatten_history(devices)

    # Connect to target database
    hook = PostgresHook('database')
    connection = hook.get_conn()

    table_name = 'airbods.public.raw'

    # Insert/update values in one transaction
    with connection.cursor() as cursor:

        # Delete old values
        sql = textwrap.dedent(f"""
        DELETE FROM {table_name}
        WHERE time_ BETWEEN '{execution_date}'
            AND '{next_execution_date}'
        """)
        LOGGER.info(sql)
        cursor.execute(sql)

        # Bulk insert values
        # https://hakibenita.com/fast-load-data-python-postgresql#execute-values-from-iterator-with-page-size
        sql = textwrap.dedent(f"""
        INSERT INTO {table_name} (
             device_id        
            ,time_
            ,air_quality
            ,co2  
            ,humidity         
            ,temperature      
            ,lorawan_datarate 
            ,lorawan_rssi     
            ,lorawan_snr      
            ,battery          
            ,pm1              
            ,pm25             
            ,pm10             
        )
        VALUES %s;
        """)
        LOGGER.info(sql)
        psycopg2.extras.execute_values(
            cur=cursor,
            sql=sql,
            argslist=((
                row['id'],
                row['time'],
                row.get('AIR_QUALITY'),
                row.get('CO2'),
                row.get('HUMIDITY'),
                row.get('TEMPERATURE'),
                row.get('LORAWAN_DATARATE'),
                row.get('LORAWAN_RSSI'),
                row.get('LORAWAN_SNR'),
                row.get('BATTERY'),
                row.get('PM1'),
                row.get('PM25'),
                row.get('PM10'),
            ) for row in rows),
            page_size=1000,
        )

    if test_mode:
        connection.rollback()
    else:
        connection.commit()


def save_data(*args, task_instance: TaskInstance, execution_date, **kwargs):
    # Get result of previous task
    raw_data = task_instance.xcom_pull('all_devices_history')

    # Build target file path
    target_dir = pathlib.Path(airflow.models.Variable.get('datacake_raw_dir'))
    filename = "{}.json".format(execution_date.isoformat())
    target_path = target_dir.joinpath(filename)

    # Serialise
    target_dir.mkdir(parents=True, exist_ok=True)
    with target_path.open('w') as file:
        file.write(raw_data)
        LOGGER.info("Wrote '%s'", file.name)
        return file.name


with airflow.DAG(
        dag_id='datacake',
        # Data collection start date 14th April 2021
        start_date=datetime.datetime(2021, 4, 14,
                                     tzinfo=datetime.timezone.utc),
        schedule_interval=datetime.timedelta(hours=1),
        description=DESCRIPTION,
) as dag:
    # Download raw data for all devices
    all_devices_history = GraphQLHttpOperator(
        http_conn_id='datacake',
        task_id='all_devices_history',
        retry_exponential_backoff=True,
        # Jinja escape characters for GraphQL syntax
        query=textwrap.dedent("""
        query {{ '{' }}
          allDevices(inWorkspace: "{{ var.value.datacake_workspace_id }}") {{ '{' }}
            id
            verboseName
            serialNumber
            history(
              fields: {{ var.value.datacake_fields }}
              timerangestart: "{{ ts }}"
              timerangeend: "{{ next_execution_date }}"
              resolution: "raw"
            )
          {{ '}' }}
        {{ '}' }}
        """),
    )

    # Save raw data to disk
    serialise_raw = PythonOperator(
        task_id='serialise_raw',
        python_callable=save_data,
        provide_context=True,
    )

    # Load raw data to database
    bulk_load = PythonOperator(
        task_id='bulk_load',
        python_callable=bulk_load_values,
        provide_context=True,
    )

    # Remove old data and insert transformed data (idempotent in a single
    # transaction)
    clean = PostgresOperator(
        task_id='clean',
        postgres_conn_id='database',
        sql=textwrap.dedent("""
        -- Defer unique constraint until so we can DELETE and then INSERT 
        -- before checking uniqueness after this atomic transaction completes.
        SET CONSTRAINTS clean_device_id_time__key DEFERRED;
        
        -- Remove old data for this time partition
        DELETE FROM airbods.public.clean
        WHERE time_ BETWEEN '{{ ts }}' AND '{{ next_execution_date.isoformat() }}';
        
        -- Insert clean data rows by transforming raw data
        WITH transformed AS (
            SELECT
                 raw.device_id
                -- Parse ISO timestamp inc. time zone
                -- Round (floor) to two-minute resolution
                -- TODO https://stackoverflow.com/a/62149151
                ,DATE_TRUNC('minute', raw.time_::timestamptz) AS time_
                ,raw.air_quality
                ,raw.co2
                ,raw.humidity
                ,raw.temperature
            FROM airbods.public.raw
            WHERE raw.time_ BETWEEN '{{ ts }}' AND '{{ next_execution_date.isoformat() }}'
        ),
        -- Group by device and time because we've rounded the time
        aggregated AS (
            SELECT
                 transformed.device_id
                ,transformed.time_
                ,MAX(transformed.air_quality) AS air_quality
                ,MAX(transformed.co2) AS co2
                ,MAX(transformed.humidity) AS humidity
                ,MAX(transformed.temperature) AS temperature
            FROM transformed
            GROUP BY transformed.device_id, transformed.time_
        )
        -- Remove null rows
        INSERT INTO airbods.public.clean
        SELECT device_id, time_, air_quality, co2, humidity, temperature
        FROM aggregated
        WHERE air_quality IS NOT NULL
            AND co2 IS NOT NULL
            AND humidity IS NOT NULL
            AND temperature IS NOT NULL;
        """),
    )

    all_devices_history >> serialise_raw
    all_devices_history >> bulk_load >> clean
