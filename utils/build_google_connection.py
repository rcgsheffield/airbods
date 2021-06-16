"""
Google Cloud connection string generator

Create a URI to represent an Airflow connection using a service account to
access the Google Cloud API.

https://airflow.apache.org/docs/apache-airflow-providers-google/2.1.0/connections/gcp.html#configuring-the-connection
"""

import pathlib
import urllib.parse

GOOGLE_CREDENTIALS = pathlib.Path.home().joinpath('airbods.json')

SCHEME = 'google-cloud-platform'

# Scopes
# https://developers.google.com/identity/protocols/oauth2/scopes#drive
SCOPES = "https://www.googleapis.com/auth/drive"

if __name__ == '__main__':
    with GOOGLE_CREDENTIALS.open() as file:
        key_json_data = file.read()

    query_params = dict(
        extra__google_cloud_platform__keyfile_dict=key_json_data,
        extra__google_cloud_platform__scope=SCOPES,
    )

    query = urllib.parse.urlencode(query_params)

    parts = (SCHEME, '', '', query, '')
    url = urllib.parse.urlunsplit(parts)

    print(url)
