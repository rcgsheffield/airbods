"""
Google Cloud connection string generator

Create a URI to represent an Airflow connection using a service account to
access the Google Cloud API.

https://airflow.apache.org/docs/apache-airflow-providers-google/2.1.0/connections/gcp.html#configuring-the-connection

https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html
"""

import pathlib
import urllib.parse
import json

CONNECTION_ID = 'google_cloud_default'

GOOGLE_CREDENTIALS = pathlib.Path.home().joinpath('airbods.json')

SCHEME = 'google-cloud-platform'

# Scopes
# https://developers.google.com/identity/protocols/oauth2/scopes#drive
SCOPES = "https://www.googleapis.com/auth/drive"


def build_url(scheme, keyfile, scopes) -> str:
    """
    Generate connection string
    """
    query_params = dict(
        google_cloud_platform__keyfile_dict=keyfile,
        google_cloud_platform__scope=scopes,
    )

    print(json.dumps(query_params))

    # Prefix
    extra = {'extra__' + key: value for key, value in query_params.items()}
    query = urllib.parse.urlencode(extra)
    parts = (scheme, '', '', query, '')
    return urllib.parse.urlunsplit(parts)


# def build_connection(keyfile) -> dict:
#     """
#     Generate connection JSON
#     """
#     import json
#     from airflow.models import Connection
#
#     conn = Connection(
#         conn_id=CONNECTION_ID,
#         conn_type=SCHEME,
#         extra=json.dumps(dict(
#             google_cloud_platform__keyfile_dict=keyfile,
#             google_cloud_platform__scope=SCOPES,
#         ))
#     )
#
#     print(conn.get_uri())
#
#     return conn


if __name__ == '__main__':
    with GOOGLE_CREDENTIALS.open() as file:
        key_json_data = file.read()

    url = build_url(scheme=SCHEME, keyfile=key_json_data, scopes=SCOPES)

    print(url)
