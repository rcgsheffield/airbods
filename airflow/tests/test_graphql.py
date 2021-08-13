"""
https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#unit-tests
"""

import unittest

import airflow.models
from airflow.utils.state import State
from operators.graphql import GraphQLHttpOperator

DAG_ID = 'test_graphql_operator'
QUERY = """
{
  user {
    id
  }
}
"""


class GraphQLTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dag = airflow.DAG(DAG_ID)
        self.op = GraphQLHttpOperator(
            http_conn_id='datacake',
            task_id='test_user',
        )
        self.ti = airflow.models.TaskInstance()

    def test_run(self):
        self.ti.run()
        self.assertEqual(self.ti.state, State.SUCCESS)
