"""
GraphQL custom Airflow operator
"""

from airflow.providers.http.operators.http import SimpleHttpOperator


class GraphQLHttpOperator(SimpleHttpOperator):
    def __init__(self, query: str, **kwargs):
        super().__init__(**kwargs)
        self.method = 'GET'
        self.query = query

    def execute(self, context: dict):
        # Build template context
        _context = self.params.copy()
        _context.update(context)
        rendered_query = self.render_template(content=self.query,
                                              context=_context)
        self.log.debug(rendered_query)
        self.data = dict(query=rendered_query)
        return super().execute(context)
