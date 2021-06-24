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

# Deployment

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
# Run a playbook
docker compose run --entrypoint ansible-playbook ansible /etc/ansible/playbooks/airbods.yaml
```

## View logs

```bash
sudo journalctl -u airflow-scheduler --since "$(date -I) 12:00"
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

1. Open the "Data" tab
2. Click "New Query"
3. Click "From Other Sources"
4. Click "From ODBC"
5. Under "Data source name (DSN)" select "PostreSQL35W" and click "OK"
6. Open the folders: `airbods` then `public` 
7. Select `clean_device` and click "Edit" to customise the query (to avoid downloading the entire database)
8. Click "Refresh Preview" to see what the data look like
9. Use the Power Query Editor to filter and transform data as required then click "Close & Load"