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


def bulk_load_values(*args, task_instance, **kwargs):
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

    connection.commit()


with airflow.DAG(
        dag_id='datacake',
        start_date=datetime.datetime(2021, 5, 17,
                                     tzinfo=datetime.timezone.utc),
        schedule_interval=datetime.timedelta(hours=1),
) as dag:
    # Download raw data for all devices
    all_devices_history = GraphQLHttpOperator(
        http_conn_id='datacake',
        task_id='all_devices_history',
        # Jinja escape characters for GraphQL syntax
        query=textwrap.dedent("""
        query {{ '{' }}
          allDevices(inWorkspace: "{{ var.value.datacake_workspace_id }}") {{ '{' }}
            id
            serialNumber
            verboseName
            location
            lastHeard
            tags
            metadata
            softwareVersion
            claimed
            claimCode
            online
            ttnDevId
            internalId
            isKemperDevice
            product {{ '{' }}
              id
              name
              slug
            {{ '}' }}
            currentMeasurements(allActiveFields:true) {{ '{' }}
              field {{ '{' }}
                id
                fieldName
                verboseFieldName
                unit
                description  
              {{ '}' }}
            {{ '}' }}
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

    # Insert or update values
    merge_devices = PostgresOperator(
        task_id='merge_devices',
        postgres_conn_id='database',
        sql=textwrap.dedent("""
        INSERT INTO
            airbods.public.device (device_id, serialnumber, verbosename, object)
        VALUES
            {% for device in task_instance.xcom_pull('all_devices_history') %}
            {% if not loop.first %},{% endif %}
            ("{{ device['id'] }}", "{{ device['serialNumber'] }}", "{{ device['verbosename'] }}", "{{ device|tojson }}")
            {% endfor %}
        ON CONFLICT (device_id)
        DO UPDATE SET device.serialnumber = EXCLUDED.serialnumber,
                      device.verbosename = EXCLUDED.verbosename,
                      device.object = EXCLUDED.object;
        """)
    )

    all_devices_history >> merge_devices
    all_devices_history >> bulk_load
