import datetime
import textwrap

import airflow.models
from airflow.operators.bash import BashOperator

from operators.graphql import GraphQLHttpOperator

DATACAKE_WORKSPACE_ID = airflow.models.Variable.get(
    'datacake_workspace_id')

with airflow.DAG(
        dag_id='airbods',
        start_date=datetime.datetime(2021, 5, 17,
                                     tzinfo=datetime.timezone.utc),
        schedule_interval=datetime.timedelta(hours=1),
) as dag:
    # Download raw data for all devices
    get_raw_data = GraphQLHttpOperator(
        http_conn_id='datacake_airbods',
        task_id='all_devices_history',
        # Jinja escape characters for GraphQL syntax
        query=textwrap.dedent("""
        query {{ '{' }}
          allDevices(inWorkspace: "{{ DATACAKE_WORKSPACE_ID }}") {{ '{' }}
            history(
              fields: ["CO2","TEMPERATURE","LORAWAN_SNR","LORAWAN_DATARATE","LORAWAN_RSSI","AIR_QUALITY","HUMIDITY"]
              timerangestart: "{{ ts }}"
              timerangeend: "{{ next_execution_date }}"
              resolution: "raw"
            ) 
          {{ '}' }}
        {{ '}' }}
        """)
    )

    # Write the result of previous task to file
    save_raw_data = BashOperator(
        task_id='save_data',
        bash_command=textwrap.dedent("""
        echo {{ ti.xcom_pull("raw_{{ id }}") }} > /{{ id }}.json
        """)
    )

    get_raw_data >> save_raw_data
