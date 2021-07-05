import datetime
import textwrap
import json
import logging

import airflow.utils.dates
from operators.graphql import GraphQLHttpOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

LOGGER = logging.getLogger(__name__)

with airflow.DAG(
        dag_id='datacake_devices',
        start_date=datetime.datetime(2021, 6, 16),
        schedule_interval=datetime.timedelta(days=1),
) as dag:
    # Download raw data for all devices
    all_devices = GraphQLHttpOperator(
        task_id='all_devices',
        http_conn_id='datacake',
        retry_exponential_backoff=True,
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
          {{ '}' }}
        {{ '}' }}
        """),
        # Parse JSON response
        response_filter=lambda response: json.loads(response.text)['data'][
            'allDevices'],
        retries=3,
    )
    # Insert or update values
    merge_devices = PostgresOperator(
        task_id='merge_devices',
        postgres_conn_id='database',
        sql=textwrap.dedent("""
        INSERT INTO
            airbods.public.device (device_id, serial_number, verbose_name, object)
        VALUES
            {% for device in task_instance.xcom_pull('all_devices') %}
            {% if not loop.first %},{% endif %}
            ('{{ device.id }}', '{{ device.serialNumber }}', 
            '{{ device.verboseName }}', '{{ device|tojson }}'::json)
            {% endfor %}
        ON CONFLICT (device_id)
        DO UPDATE SET serial_number = EXCLUDED.serial_number,
                      verbose_name = EXCLUDED.verbose_name,
                      object = EXCLUDED.object;
        """)
    )

    all_devices >> merge_devices
