"""
Airbods database

Retrieve data from the PostgreSQL database using SQLAlchemy and Pandas
"""

from getpass import getpass

import pandas as pd
import sqlalchemy.engine.url

USERNAME = ''  # ENTER YOUR USERNAME HERE
HOST = 'airbods.my-domain.com'
DATABASE = 'airbods'

url = sqlalchemy.engine.url.URL(
    drivername='postgresql',
    username=USERNAME or input('Enter username: '),
    password=getpass('Enter password for {}@{}: '.format(USERNAME, HOST)),
    host=HOST,
    database=DATABASE,
)

# Build connection string
engine = sqlalchemy.create_engine(url)
sql = """
SELECT
   serial_number
  ,verbose_name
  ,time_europe_london
  ,area
  ,room
  ,air_quality
  ,co2
  ,humidity
  ,temperature
FROM reading
WHERE time_europe_london BETWEEN '2021-07-09' AND '2021-07-10'
  AND site LIKE '%Crucible%'
"""
df = pd.read_sql(sql, engine)

df.info()

print(df.head())

# Export to CSV
filename = "airbods_{}.csv".format(pd.Timestamp.now().isoformat())
df.to_csv(filename)

# Export to Excel
# df.to_excel('airbods.xlsx')
