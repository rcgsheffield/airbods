import datetime
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

LOGGER = logging.getLogger(__name__)


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


def bulk_load_values(*args, task_instance, test_mode: bool = False, **kwargs):
    # Get result of previous task
    devices = task_instance.xcom_pull('all_devices_history')

    # Convert GraphQL response to data rows
    rows = flatten_history(devices)

    # Connect to target database
    hook = PostgresHook('database')
    connection = hook.get_conn()

    # Bulk insert values
    # https://hakibenita.com/fast-load-data-python-postgresql#execute-values-from-iterator-with-page-size
    with connection.cursor() as cursor:
        psycopg2.extras.execute_values(
            cur=cursor,
            sql="""
            INSERT INTO airbods.public.raw (
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
            """,
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

    if not test_mode:
        connection.commit()


with airflow.DAG(
        dag_id='datacake',
        start_date=datetime.datetime(2021, 6, 7,
                                     tzinfo=datetime.timezone.utc),
        schedule_interval=datetime.timedelta(hours=1),
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
              fields: ["CO2","TEMPERATURE","AIR_QUALITY","HUMIDITY","LORAWAN_SNR","LORAWAN_DATARATE","LORAWAN_RSSI"]
              timerangestart: "{{ ts }}"
              timerangeend: "{{ next_execution_date }}"
              resolution: "raw"
            )
          {{ '}' }}
        {{ '}' }}
        """),
        # Parse JSON response
        response_filter=lambda response: json.loads(response.text)['data'][
            'allDevices'],
    )

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

    all_devices_history >> bulk_load >> clean
