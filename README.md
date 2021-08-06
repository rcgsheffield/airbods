# Airbods

Data pipelines and data storage for Airbods air measurement experiments.

This document contains some descriptions of how the system is built and how to administer and maintain it.

The data are described in the [Metadata](#Metadata) section below.

Code examples are contained the the [`examples`](examples) directory.

# Overview

[Architecture diagram](https://drive.google.com/file/d/1gzuFhhOR7JmASPKYVPKwvyLrUiUHpojA/view?usp=sharing)

# Usage

The system comprises several services.

## View service status

```bash
systemctl status airflow-webserver
systemctl status airflow-scheduler
systemctl status airflow-worker
systemctl status postgresql
systemctl status redis
```

## View logs

```bash
# View systemd logs
sudo journalctl -u airflow-worker --since "$(date -I)"
sudo journalctl -u airflow-webserver --since "$(date -I)"
sudo journalctl -u airflow-scheduler --since "$(date -I) 12:00"

# View PostgreSQL cluster status
pg_lsclusters

# View PostgreSQL logs
sudo systemctl status postgresql
sudo ls -l /var/log/postgresql
sudo tail /var/log/postgresql/postgresql-12-main.log
```

## Airflow CLI

Airflow [Using the Command Line Interface](http://airflow.apache.org/docs/apache-airflow/stable/usage-cli.html#)

```bash
# Log in as system user
sudo su - airflow

/opt/airflow/bin/airflow --help

# List users
/opt/airflow/bin/airflow users list

# List DAGs
/opt/airflow/bin/airflow dags list
```

## Worker monitoring

You can look at the workers using [Flower](https://flower.readthedocs.io/en/latest/), a celery monitoring tool.

1. SSH tunnel to port 5555 to 127.0.0.1:5555
2. Open `http://localhost:5555/`

## Message broker management console

SSH tunnel 15672 to 127.0.0.1:15672

```
http://localhost:15672/
```

## Container environment

This is for development purposes only.

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

# Deployment

Ansible [Executing playbooks for troubleshooting](https://docs.ansible.com/ansible/latest/user_guide/playbooks_startnstep.html)

The private key must be installed and configured on the target machine so that the control node may connect using SSH. For example:

```bash
sa_cs1jsth@airbodsdev:~$ sudo ls -l /root/.ssh
-rw-r--r-- 1 root root 109 Jun 22 16:35 authorized_keys
-rw------- 1 root root 464 Jun 22 16:35 id_rsa
sa_cs1jsth@airbodsdev:~$ ls -l /home/airflow/.ssh
-rw-r--r-- 1 airflow airflow 109 Jun 24 12:54 authorized_keys
-rw------- 1 airflow airflow 464 Jun 24 12:54 id_rsa
```

Check Ansible is working:

```bash
# View Ansible package version
docker compose run ansible --version

# View inventory
docker compose run ansible all --list-hosts

# Ping nodes
docker compose run ansible all -m ping

# Run a custom command
docker compose run ansible all -a "echo OK"

# Check a playbook
docker compose run --entrypoint ansible-playbook ansible --check /etc/ansible/playbooks/test.yaml
```

Install services:

```bash
docker compose run --entrypoint ansible-playbook ansible /etc/ansible/playbooks/airbods.yaml
```

Run automated tests:

```bash
docker compose run --entrypoint ansible-playbook ansible /etc/ansible/playbooks/test.yaml
```

# Data access

Code examples are contained the the [`examples`](examples) directory.

## Open Database Connectivity (ODBC)

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

## Excel

To use Excel to connect to the database, you need an ODBC connection or DSN. You need the ODBC driver for PostgreSQL installed to do this.

1. Open the "Data" tab
2. Click "New Query"
3. Click "From Other Sources"
4. Click "From ODBC"
5. Under "Data source name (DSN)" select "PostreSQL35W" and click "OK"
6. Open the folders: `airbods` then `public` 
7. Select `reading` (or another item) and click "Edit" to customise the query (to avoid downloading the entire database)
8. Click "Refresh Preview" to see what the data look like
9. Use the Power Query Editor to filter and transform data as required then click "Close & Load"

# Database administration

The PostgreSQL database can be administered using [psql](https://www.postgresql.org/docs/13/app-psql.html).

```bash
# Log in as database user
su - postgres
psql
# List databases
psql -c "\l"
```

## User management

A database role exists for end users called `researcher`.

Create new user credentials using the [createuser](https://www.postgresql.org/docs/current/app-createuser.html) shell command:

```bash
createuser --pwprompt --role=researcher
```

You could also do this using [CREATE ROLE](https://www.postgresql.org/docs/13/sql-createrole.html):

```sql
-- CREATE USER joe_bloggs LOGIN PASSWORD 'ChangeMe' IN ROLE researcher;
```

Role membership can also be [managed](https://www.postgresql.org/docs/13/role-membership.html) for existing users.

# Data pipeline management

The data pipelines are managed using [Apache Airflow](https://airflow.apache.org/docs/apache-airflow/stable/index.html).

## Airflow command line interface

To run these commands, you must log in as the user `airflow`:

```bash
sudo su - airflow
```

## Clear

The state of failed tasks may be cleared using the GUI under Browse > DAG Runs. You can also use the CLI with the [tasks clear](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#clear) command. This may be applied to an entire DAG run, or a subset of tasks, for a specified time range.

```bash
/opt/airflow/bin/airflow tasks clear $DAG_ID --start-date "YYYY-MM-DD" --end-date "YYYY-MM-DD"
```

## Backfill

Using the Airflow CLI, use the [backfill command](https://airflow.apache.org/docs/apache-airflow/stable/dag-run.html#backfill) (see [CLI backfill docs](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#backfill)) to run historic data pipelines:

```bash
# /opt/airflow/bin/airflow dags backfill $DAG_ID -s $START_DATE -t <task_regex>
/opt/airflow/bin/airflow dags backfill datacake -s 2021-04-15 --verbose
```

# Metadata

The following are the items in the database. There are two types of object: tables and views. Tables contain rows of data and views are predefined SQL queries that display, merge or process that data in a certain way.

The SQL DDL used to define and create this schema is contained in SQL files in the directory [ansible/playbooks/files/database](./ansible/playbooks/files/database) and is run by the deployment script.

## Tables

* `raw` contains a copy of the original data retrieved from Datacake. It unadvisable to use this data for research analysis, use `clean` or one of the views instead. Each row corresponds to a data capture reading by a sensor at a certain time. It has a timestamp column, several columns describing the sensor used and one column per metric.
* `clean` contains the transformed data, taken from `raw`, that is ready for use
* `device` contains one row per sensor and has the following columns:
  * `device_id` is a unique identifier created by Datacake, one per sensor entry on that platform. You can view the information about a device using its URL: `https://app.datacake.de/airbods/devices/d/<device_id>`
  * `serial_number` is the serial number taken from the physical device. This is the best way to uniquely identify a sensor because it won't change.
  * `verbose_name` is a human-readable label applied to each device which change over time.
  * `object` contains a JSON object with all the additional device information stored on Datacake.
* `deployment` contains one row for each time a sensor is moved to a new location for a period of time. There may be multiple rows per device, one for each combination of location and time period. The `serial_number` column maps to the column of the same name on the `device` table. The `start_time` is the time when the device was deployed. The `end_time` is when this deployment ended, or is blank if this deployment continues. The other columns describe the location of the deployment.

## Views

* `reading` merges the tables `clean`, `device` and `deployment` to present the context for each clean data row, in addition to calculating some aggregated statistics. The deployment information is taken from the relevant deployment for that sensor at the time the reading was recorded. It contains the following columns:
  * `serial_number` is the sensor identifier.
  * `time_utc` and `time_europe_london` is the time of each reading, displayed in each time zone
  * `city`, `site`, `area` etc. are columns from the `deployment` table describing the sensor location.
  * `air_quality`, `co2` and other physical measurements
  * `co2_room_min`, `humidity_area_mean`, `temperature_room_max` and other similar columns contain the aggregate statistics for each metric, partitioned over the location and day. The aggregate functions are the minimum `min`, average `mean` and maximum `max` for that deployment.
* `device_deployment` merges the tables `device` and `deployment` but contains one row per sensor for *latest* deployment. The columns are the same as those on the two source tables.