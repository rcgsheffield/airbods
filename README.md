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

