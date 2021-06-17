# Airbods

Data pipelines and data storage for Airbods air measurement experiments.

# Usage

```bash
# Build images (and update remote images)
docker-compose build --pull
# Start services
docker-compose up -d --remove-orphans
# View status
docker-compose ps
```

# Testing

See [Testing a DAG](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#testing-a-dag).

To check that the DAG code may be imported:

```bash
docker-compose exec worker python dags/datacake.py
```

Test a specific task:

```bash
# docker-compose exec <service> airflow task test <dag_id> <task_id> <date>
docker-compose exec worker airflow tasks test datacake all_devices_history 2021-06-01
```

Run unit tests:

```bash
docker-compose exec worker python -m unittest --failfast
```

# ODBC

To install the PostgreSQL ODBC driver for Windows:

1. Visit the [psqlODBC - PostgreSQL ODBC driver](https://odbc.postgresql.org/) page
2. Click on the [PostgreSQL downloads site](http://www.postgresql.org/ftp/odbc/versions/)
3. For Windows, select `msi`
4. Scroll down to the latest version, which is `psqlodbc_13_01_0000.zip` at the time of writing
5. Download and install this driver
6. Open the ODBC Data Source Administrator via the start menu or by running `odbcad32`
7. Create a DSN:
   1. Click "Add"
   2. Select "PostgreSQL Unicode" and click "Finish"
   3. Enter the following values:
      1. Database: `airbods`
      2. Server: `airbods.shef.ac.uk`
      3. Username: `<your user name>`
      4. Password: `<your password>`

# Excel

To use Excel to connect to the database, you need an ODBC connection or DSN. You need the ODBC driver for PostgreSQL installed to do this.

1. In Excel, click the "Data" tab and select "From Other Sources" -> "From Data Connection Wizard".
2. Select ODBC DSN and click "Next"
3. Select the DSN you created before (the default name is `PostreSQL35W`) and click "Next"
4. Select `clean_device` or another table