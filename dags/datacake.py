import datetime
import textwrap
import json

import airflow.models
import psycopg2.extras

from operators.graphql import GraphQLHttpOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator


def bulk_load_values(*args, task_instance, **kwargs):
    data = task_instance.xcom_pull('all_devices_history')

    # Convert GraphQL response to data rows
    rows = (
        dict(
            device_id=device['id'],
            **json.loads(device['history'])
        )
        for device in data['data']['allDevices'])

    hook = PostgresHook('database')

    connection = hook.get_conn()

    # https://hakibenita.com/fast-load-data-python-postgresql#execute-values-from-iterator-with-page-size
    with connection.cursor() as cursor:
        psycopg2.extras.execute_values(
            cur=cursor,
            sql="INSERT INTO airbods.public.raw VALUES %s;",
            arglist=((
                row['device_id'],
                row['time'],
                row.get('air_quality'),
                row.get('co2'),
                row.get('humidity'),
                row.get('temperature'),
                row.get('lorawan_datarate'),
                row.get('lorawan_rssi'),
                row.get('lorawan_snr'),
                row.get('battery'),
                row.get('pm1'),
                row.get('pm25'),
                row.get('pm10'),
            ) for row in rows),
            page_size=1000,
        )


with airflow.DAG(
        dag_id='datacake',
        start_date=datetime.datetime(2021, 5, 17,
                                     tzinfo=datetime.timezone.utc),
        schedule_interval=datetime.timedelta(hours=1),
) as dag:
    # Download raw data for all devices
    get_raw_data = GraphQLHttpOperator(
        http_conn_id='datacake',
        task_id='all_devices_history',
        # Jinja escape characters for GraphQL syntax
        query=textwrap.dedent("""
        query {{ '{' }}
          allDevices(inWorkspace: "{{ var.value.datacake_workspace_id }}") {{ '{' }}
            id
            history(
              fields: ["CO2","TEMPERATURE","AIR_QUALITY","HUMIDITY","LORAWAN_SNR","LORAWAN_DATARATE","LORAWAN_RSSI"]
              timerangestart: "{{ ts }}"
              timerangeend: "{{ next_execution_date }}"
              resolution: "raw"
            )
          {{ '}' }}
        {{ '}' }}
        """),
    )

    bulk_load = PythonOperator(
        task_id='bulk_load',
        python_callable=bulk_load_values,
        provide_context=True,
    )

    get_raw_data >> bulk_load
