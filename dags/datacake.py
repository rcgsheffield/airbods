import datetime
import textwrap

import airflow.models

from operators.graphql import GraphQLHttpOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator


def bulk_load_values(*args, task_instance, **kwargs):
    data = task_instance.xcom_pull('all_devices_history')


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
            history(
              fields: ["CO2","TEMPERATURE","LORAWAN_SNR","LORAWAN_DATARATE","LORAWAN_RSSI","AIR_QUALITY","HUMIDITY"]
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
