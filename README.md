# Airbods

Data pipelines and data storage for Airbods air measurement experiments. The primary data pipeline downloads all the raw data available on a single Datacake "workspace" (specified by its unique identifier) and copies those data onto a database. It then transforms that data to make a "clean" data set available for research use.

This document contains some descriptions of how the system is built and how to administer and maintain it.

The data are described in the [Metadata](#Metadata) section below.

Code examples are contained the the [`examples`](examples) directory that can be used to retrieve data in various languages.#

This repository contains an Ansible project as described below.

# Overview

There is an **overview of the system in the [architecture diagram](https://drive.google.com/file/d/1gzuFhhOR7JmASPKYVPKwvyLrUiUHpojA/view?usp=sharing)**.

The system comprises two major parts:

* **Workflow Orchestrator:** The data pipelines are implemented using a workflow orchestrator called [Apache Airflow](https://airflow.apache.org/).
* **Database:** The data are stored in a relational database management system implemented using [PostgreSQL](https://www.postgresql.org/).
  * A web-based [database administration interface](https://airbods.shef.ac.uk/pgadmin4) is available to manage this database.

The workflow orchestrator comprises the subcomponents inside the black dotted line. The user roles are represented by red person icons. The cloud services are shown as blue clouds. The services are represented as green rectangles. The databases are shown as yellow cylinders.

There are three typical user roles:

* End user (researcher) will access the SQL database using a certain security role.
* Data engineer will access the workflow orchestrator using its web portal.
* A system administrator will access the virtual machine(s) on which the system runs.

## Workflow orchestrator

The data pipelines are defined using three directed acyclic graphs (DAGs) that are defined in `airflow/dags/*.py`.

* `datacake` downloads, stores and transforms data retrieved via the Datacake API.
* `datacake_devices` retrieves and stores metadata about sensors from the Datacake API
* `deployments` retrieves and stores information about sensors and their deployments at certain locations from a Google Sheets spreadsheet.

The configuration for these is stored in `airflow/variables.json`.

There is a custom operator used to access [GraphQL](https://graphql.org/) APIs via HTTP in `airflow/plugins/operators/graphql.py` that is used in the workflows that interact with Datacake, which exposes this kind of API.

## Database

The RDMS service contains three databases:

* `airbods` contains the research data and is accessible by the end users. The tables are described in the metadata section below.
* `airflow` contains the metadata and system data for the workflow orchestrator. This may be accessed by the user account (role) named `airflow`.
* `postgres` contains system data for the database service itself

The database settings are specified in the Ansible playbook and the configuration files `postgresql.conf` and `pg_hba.conf` as discussed in the [PostgreSQL  12 documentation](https://www.postgresql.org/docs/12/index.html).

# Installation

The system comprises multiple subsystems as described above that are installed using an automated deployment tool to facilitate continuous integration/continuous deployment (CICD).

## Ansible

Automated deployment is implemented using [Ansible](https://docs.ansible.com/), which defines a workflow comprising a series of tasks that install software and configure services. This workflow is executed on one or more remote machines. See their docs: [Executing playbooks for troubleshooting](https://docs.ansible.com/ansible/latest/user_guide/playbooks_startnstep.html). Most of the service configuration files are in the `files` directory (Ansible will automatically search this directory for files to upload.) Variables are defined in the  `group_vars/all` YAML file.

You may need to [install Ansible in a Python virtual environment](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#id18) if you need to use a more up-to-date version of the software, which is written in Python. To use the tool you'll need to activate the virtual environment with a command similar to the one below, assuming the environment was created in the directory `~/ansible`:

```bash
source ~/ansible/bin/activate
```

## Key generation

Security keys, certificate requests and certificates may be generated using `openssl`. Certificate-authority-signed certificates were retrieved via ITS Helpdesk. This is particularly important for the SQL database because this service will be exposed to the risks associated with access via the public internet.

### Airflow webserver

Generate key and certificate:

```
openssl req -nodes -x509 -newkey rsa:4096 -keyout secrets/webserver_key.pem -out secrets/webserver.pem -days 365
```

`-nodes` means "No DES" or an unencrypted private key which has no password.

## Deployment

The deployment script installs the necessary software subsystems on a remote machine. The script should be idempotent so it can be run repeatedly without causing problems.

### Secure shell access

The private key must be installed and configured on the target machine so that the control node may connect using secure shell (SSH). See this tutorial: [How To Configure SSH Key-Based Authentication on a Linux Server](https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server). The `ssh-copy-id` tool is useful here to install your key information on a remote host.

```bash
ssh-copy-id $USER@airbods.shef.ac.uk
ssh-copy-id $USER@airbods01.shef.ac.uk
ssh-copy-id $USER@airbods02.shef.ac.uk
```

You can view the installed files like so:

```bash
ssh $USER@airbods.shef.ac.uk -i ~/.ssh/id_rsa "ls -la ~/.ssh/"
```

The `ida_rsa` file is that user's private key. The `authorized_keys` file is used to list the public keys that can automatically connect. These files would be stored in the directory `~/.ssh` for the user you use to connect.

You can test the connection like so:

```bash
ssh $USER@airbods.shef.ac.uk -i ~/.ssh/id_rsa "echo OK"
```

The tool `ssh-agent` is useful to save time by storing the password for encrypted private keys so you don't have to repeatedly type it in. See the Ansible [docs connection info](https://docs.ansible.com/ansible/latest/user_guide/connection_details.html).

```bash
ssh-agent bash
ssh-add ~/.ssh/id_rsa
```

### Superuser access

It's assumed that you log into the remote system as a user (with username `$USER`) that is a member of the system administrator's group `airbodsadmins`. Contact the ITS Unix team with queries about this.

You'll also need to be able to run executables as other users. To test this, try to run the following commands (which will only work after the relevant users have been created.)

```bash
sudo -u postgres id
sudo -u airflow id
```

### Running Ansible

The variable `$USER` is used to specify which username to use to connect to the remote host.

```bash
USER=<sa_username>
```

Use the shell variable `$INVENTORY` to select the target environment:

```bash
INVENTORY=hosts-dev.yaml
#INVENTORY=hosts-prod.yaml
```

Check Ansible is working. (You probably need to use `ssh-agent` as described above.)

```bash
# View Ansible package version
ansible --version

# View inventory
ansible --inventory $INVENTORY --list-hosts all

# Ping all remote hosts
ansible --inventory $INVENTORY --user $USER all -m ping

# Run a custom command on each host
ansible --inventory $INVENTORY --user $USER -a "echo OK" all
```

To run the deployment script, we need to use the deployment script which is defined as an Ansible "playbook" using the `ansible-playbook` command (see [ansible-playbook CLI docs](https://docs.ansible.com/ansible/latest/cli/ansible-playbook.html)).

The `--inventory` option determines which [inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html) of hosts will be targeted, where `hosts.yaml` contains the development environment and `hosts-prod.yaml` points to the production environment. You need to use a different inventory file which will point the deployment script to a different machine using the `--inventory` argument of the `ansible-playbook` command.

```bash
# Check that the Ansible Playbook command is working
ansible-playbook --version

# Check a playbook
ansible-playbook --inventory $INVENTORY --user $USER --ask-become-pass airbods.yaml --check
```

Install services (inside the selected environment):

```bash
ansible-playbook --inventory $INVENTORY --user $USER --ask-become-pass airbods.yaml
```

Run automated tests:

```bash
ansible-playbook --inventory $INVENTORY --user $USER --ask-become-pass test.yaml
```

### Troubleshooting

If problems occur, check the logs and try the following steps:

* Re-run the deployment script
* Check service status (see the Monitoring section below) and logs.
* Check that each service can connect to the other relevant services.
* Ensure that the Ansible [notify handler](https://docs.ansible.com/ansible/latest/user_guide/playbooks_handlers.html) feature is enabled for any changes you may have have made.
* Restart the services on the remote host (or perhaps reboot the entire remote system manually)
* Use Ansible's verbose mode and other [debugging features](https://docs.ansible.com/ansible/latest/user_guide/playbooks_debugger.html)

### Scaling

Currently this deployment is designed to run a single machine, assuming that it's a small-scale instance. To scale this up to multiple machines, the hosts and deployment script will need to be adapted so that each machine performs a different role.

## Maintenance

Routine maintenance must be performed on the server operating system and the various services that make up the system. There is a script called `maintenance.yaml` to automate some of this. This can be run as follows:

```bash
ansible-playbook --inventory hosts-prod.yaml --user $USER --ask-become-pass maintenance.yaml
```

This will clear out various aspects of the system but isn't a substitute for a proper maintenance routine.

# Usage

There are several ways to interact with and control each part of the system.

## SQL database

There are several ways to connect to the database, either using software packages or programming languages. See the [examples](examples) directory for a list of available tools.

The [connection string](https://www.postgresql.org/docs/12/libpq-connect.html#LIBPQ-CONNSTRING) is as follows:

```uri
postgresql://$USERNAME:$PASSWORD@airbods.shef.ac.uk/airbods
```

### PostgreSQL interactive terminal

You can connect to the database with [psql](https://www.postgresql.org/docs/12/app-psql.html) as follows:

```bash
psql --host=airbods.shef.ac.uk --dbname=airbods --username=$USERNAME
```

You may need to change the username to something else. You can enter the password manually or use a [pgpass](https://www.postgresql.org/docs/12/libpq-pgpass.html) file.

You can run a command by using the shell or as follows:

```bash
psql --host=airbods.shef.ac.uk --dbname=airbods --username=$USERNAME --command "SELECT now();"
```

### Backup

See PostgreSQL docs [Chapter 25. Backup and Restore](https://www.postgresql.org/docs/12/backup.html).

```bash
# Log in with database service account
sudo su - postgres --shell /bin/bash

pg_dump -h airbods.shef.ac.uk airbods > airbods.sql
```

## Airflow CLI

You can use the Airflow [Using the Command Line Interface](http://airflow.apache.org/docs/apache-airflow/stable/usage-cli.html#) to view, control and administer the workflow orchestrator. You should run this tool as the service user `airflow` or as `root`.

```bash
# Log in as system user (or use sudo -u airflow <command>)
sudo su - airflow

/opt/airflow/bin/airflow --help

# List users
/opt/airflow/bin/airflow users list

# List DAGs
/opt/airflow/bin/airflow dags list
```

# Testing

## Airflow

See [Testing a DAG](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#testing-a-dag).

To check that the DAG code may be imported:

```bash
python dags/datacake.py
```

Test a specific task:

```bash
airflow task test <dag_id> <task_id> <date>
airflow tasks test datacake all_devices_history 2021-06-01
```

Run unit tests:

```bash
python -m unittest --failfast
```

# Data access

Code examples are contained the the [`examples`](examples) directory.

# Database administration

The database service may be controlled using `systemd`:

```bash
# Restart PostgreSQL service
sudo systemctl restart postgresql
```

To connect to the SQL database, see code [examples](examples).

## pgAdmin web interface

The [pgAdmin](https://www.pgadmin.org/) tool is available by opening [airbods.shef.ac.uk](https://airbods.shef.ac.uk/) using a web browser.

### Configure server

The connection to the database must be configured using the [Server Dialogue](https://airbods.shef.ac.uk/help/help/server_dialog.html).

1. If no servers are configured, click "Create Server"
2. On the "General" tab, populate these fields:
   1. Name: `Airbods`
   2. Shared: `Yes`
3. On the "Connection" tab, populate these fields:
   1. Host name: `localhost`
   2. Username: `pgadmin`
   3. Password: `***************` (this must be kept secret)
   4. Save password: `Yes`
4. Click "Save"

### Add pgAdmin user

These user accounts are used to access pgAdmin only (not the SQL database itself.)

1. Once logged in, to open the [User Management](https://www.pgadmin.org/docs/pgadmin4/latest/user_management.html) panel, click on the arrow in the top-right corner of the screen.
2. Click "Users"
3. Click the "+" icon on the top-right of the "User Management" window
4. Fill in the form fields
   1. Email
   2. Role = Administrator
5. hit "Enter"

### Create users using pgAdmin

Follow the steps below to create a new login (user credentials) to access the SQL database.

1. Log into the pgAdmin tool
2. On the browser (left pane) select the Airbods server
3. Right-click on the server and click on "Create" -> "Login/Group Role"
4. On the first tab called "General" in the name field, enter a username (don't use special characters)
5. On the second tab, "Definition," enter a unique password
6. On the "Privileges" tab, set "Can login?" to "Yes"
7. On the "Membership" tab, next to "Member of" click on the "Select roles" box and select the "researcher" role.
8. Click "Save"

As a check, the SQL tab should show something like this:

```sql
CREATE ROLE joebloggs WITH
	LOGIN
	NOSUPERUSER
	NOCREATEDB
	NOCREATEROLE
	INHERIT
	NOREPLICATION
	CONNECTION LIMIT -1
	PASSWORD 'xxxxxx';
	
GRANT researcher TO joebloggs;
```

## PostgreSQL CLI

The PostgreSQL database can be administered using [psql](https://www.postgresql.org/docs/13/app-psql.html).

```bash
sudo -u postgres psql
# List databases
sudo -u postgres psql -c "\l"
# List users
sudo -u postgres psql -c "\du"
```

## User management

A database role exists for end users called `researcher`.

### Create users using the CLI

Create new user credentials using the [createuser](https://www.postgresql.org/docs/current/app-createuser.html) shell command:

```bash
createuser --pwprompt --role=researcher
```

You could also do this using [CREATE ROLE](https://www.postgresql.org/docs/13/sql-createrole.html):

```sql
CREATE USER joebloggs LOGIN PASSWORD 'xxxxxx' IN ROLE researcher;
```

Role membership can also be [managed](https://www.postgresql.org/docs/13/role-membership.html) for existing users.

# Data pipeline management

The data pipelines are managed using [Apache Airflow](https://airflow.apache.org/docs/apache-airflow/stable/index.html). See the [Airflow tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html).

## Airflow web interface

The is an Airflow GUI available via the [webserver](https://airflow.apache.org/docs/apache-airflow/stable/security/webserver.html) service which is available via SSH tunnel. To test that this is available using `curl` using the command below, the `--insecure` flag is used to prevent the certificate being checked (because the certificate used is not signed by a certificate authority (CA) and is self-signed.) To view this interface in your web browser you'll need to skip any security warning messages about this certificate issue.

```bash
# Create SSH tunnel
ssh -L 4443:127.0.0.1:4443 $USER@airbods01.shef.ac.uk
```

This can be opened at this URL: https://localhost:4443

You can check it's worked by running this command from your local machine:

```bash
# Check the web page is accessible
curl --insecure --head https://localhost:4443
```

The DAG calendar view is useful to give an overview of the entire history of the workflow.

## Airflow command line interface

To run these commands, you must log in to a worker machine and run the following commands as the user `airflow` (that is, prefix the commands with `sudo -u airflow` to run them as that service user.)

```bash
# Log in as Airflow service user
sudo su - airflow --shell /bin/bash

# Add the Airflow binary directory to the shell context ($PATH)
export PATH="/opt/airflow/bin:$PATH"
```

To check it's working:

```bash
# Check Airflow CLI is working as expected
airflow version

# Get environment information
airflow info

# Check the metadata database connection
airflow db check
```

### List workflows

To show the available workflows:

```bash
airflow dags list
```

### Clear

The state of failed tasks may be cleared using the GUI under Browse > DAG Runs. You can also use the CLI with the [tasks clear](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#clear) command. This may be applied to an entire DAG run, or a subset of tasks, for a specified time range.

```bash
# Clear *all* tasks within a time range
#airflow tasks clear --start-date "YYYY-MM-DD" --end-date "YYYY-MM-DD" datacake
```

To only clear failed tasks:

```bash
airflow tasks clear datacake --only-failed
```

### Backfill

Using the Airflow CLI, use the [backfill command](https://airflow.apache.org/docs/apache-airflow/stable/dag-run.html#backfill) (see [CLI backfill docs](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html#backfill)) to run historic data pipelines:

```bash
# airflow dags backfill $DAG_ID -s $START_DATE -e $END_DATE -t <task_regex>
airflow dags backfill datacake --start-date "$START_DATE" --end-date "$(date -I)"
```

# Datacake

The workflows use the Datacake [GraphQL API](https://docs.datacake.de/api/graphql-api), which communicates over authenticated HTTPS. Please read those documents for an introduction to using this. This is implemented using an Airflow [custom operator](https://airflow.apache.org/docs/apache-airflow/stable/howto/custom-operator.html) called `GraphQLHttpOperator` which is a subclass of the built-in `SimpleHttpOperator`. There is a browser-based interface at https://api.datacake.co/graphql/ where you need to input the access token and you can run test GraphQL queries.

The raw data are stored on the virtual machine in the directory `/home/airflow/data` as JSON files, one for each hourly batch operation.

# Metadata

The following are the items in the database. There are two types of object: tables and views. Tables contain rows of data and views are predefined SQL queries that display, merge or process that data in a certain way.

The SQL DDL used to define and create this schema is contained in SQL files in the directory [ansible/playbooks/files/database](files/database) and is run by the deployment script.

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
  * `co2_zone_min`, `humidity_area_mean`, `temperature_zone_max` and other similar columns contain the aggregate statistics for each metric, partitioned over the location and day. The aggregate functions are the minimum `min`, average `mean` and maximum `max` for that deployment. The location may be the zone and area where the sensor was deployed. The day is the calendar date in UTC (GMT).
* `device_deployment` merges the tables `device` and `deployment` but contains one row per sensor for *latest* deployment. The columns are the same as those on the two source tables.

# Quality Assurance

There are a number of ways to check the validity and integrity of the data in the database.

To check the time range of the raw data:

```sql
SELECT DISTINCT left(raw.time_, 10) AS day
FROM airbods.public.raw
ORDER BY 1;
```

Similarly for the days in the clean data:

```sql
SELECT DISTINCT clean.time_::DATE AS day
FROM airbods.public.clean
ORDER BY 1;
```

# Monitoring

The system comprises several services which are managed using `systemd`.

## View service status

You can view the status of the services using the following commands:

```bash
systemctl status airflow-webserver
systemctl status airflow-scheduler
systemctl status airflow-worker
systemctl status redis

# RabbitMQ
sudo systemctl status rabbitmq-server
sudo -u rabbitmq rabbitmq-diagnostics status

# View PostgreSQL cluster status
systemctl status postgresql
pg_lsclusters

# pgAdmin4 web server
sudo systemctl status apache2

# Airflow
sudo -u airflow /opt/airflow/bin/airflow info
```

## View logs

Service logs are available using the `journalctl` command. The `---since` option is used to filter by time.

```bash
# Airflow service logs
sudo journalctl -u airflow-worker --reverse # most recent first
sudo journalctl -u airflow-webserver --since "$(date -I)"  # current day
sudo journalctl -u airflow-scheduler --since "$(date -I) 12:00" # this afternoon
```

PostgreSQL database service logs:

```bash
sudo systemctl status postgresql
# List available log files (they're rotated regularly)
sudo ls -l /var/log/postgresql
sudo tail /var/log/postgresql/postgresql-12-main.log
```

pgAdmin logs:

```bash
sudo journalctl -u gunicorn --since "1 hour ago"
```

RabbitMQ message broker service logs:

```bash
sudo journalctl -u rabbitmq-server --since "1 hour ago"

# View logs for a particular node
sudo -u rabbitmq tail /var/log/rabbitmq/rabbit@localhost.log

# List RabbitMQ log files
ls -lt  /var/log/rabbitmq/

# List RabbitMQ crash log files
sudo ls -lt  /var/log/rabbitmq/log/
```

Redis database service logs:

```bash
sudo journalctl -u redis --since "$(date -I)"
```

## System resource utilisation

Task summary

```bash
top
```

Processor-related statistics:

```bash
mpstat
```

Memory usage in MB:

```bash
free --mega
```

Memory usage by process:

```bash
htop --sort-key PERCENT_MEM
```

Storage space usage

```bash
df -h
```

There are several tools to analyse disk usage, such as `ncdu`:

```bash
sudo apt install ncdu
sudo ncdu /home
```

## Worker monitoring

You can look at the workers and tasks using [Flower](https://flower.readthedocs.io/en/latest/), a celery monitoring tool. (Also see [Airflow Flower docs](https://airflow.apache.org/docs/apache-airflow/stable/security/flower.html).) This can be accessed using an SSH tunnel for port 5555:

```bash
ssh -L 5555:127.0.0.1:5555 $USER@airbods01.shef.ac.uk
```

 Then open http://localhost:5555 in a web browser on your computer.

## Message broker

See: RabbitMQ `rabbitmqctl` and [Management Command Line Tool](https://www.rabbitmq.com/management-cli.html). Examples:

```bash
# Check it's installed
sudo -u rabbitmq rabbitmqctl version

# View node status
sudo -u rabbitmq rabbitmqctl status

# List users
sudo -u rabbitmq rabbitmqctl list_users
```

### Management console

SSH tunnel port 15672 on the remote machine 127.0.0.1:15672 using the `ssh` command or `putty`.

```bash
ssh -L 15672:127.0.0.1:15672 $USER@airbods01.shef.ac.uk
```

Then open http://localhost:15672 on your local machine.

### Troubleshooting

See RabbitMQ docs [Troubleshooting Guidance](https://www.rabbitmq.com/troubleshooting.html).

If there is a problem, try restarting the service:

```bash
sudo systemctl restart rabbitmq-server
```

# Security certificates

Check that private key fingerprint matches that of the certificate:

```bash
openssl rsa -noout -modulus -in secrets/airbods_shef_ac_uk.key
openssl req -noout -modulus -in secrets/airbods_shef_ac_uk.csr
openssl x509 -noout -modulus -in files/airbods_shef_ac_uk_cert.cer
```

Check certificate expiration dates:

```bash
openssl x509 -noout -dates -in secrets/webserver.pem
openssl x509 -noout -dates -in files/airbods_shef_ac_uk_cert.cer
```

# Load balancer

The ITS load balancer `airbods-lb.shef.ac.uk` points to https://airbods.shef.ac.uk:443.