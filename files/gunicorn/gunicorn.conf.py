# Gunicorn configuration file
# https://docs.gunicorn.org/en/latest/configure.html#configuration-file

# Available settings:
# https://docs.gunicorn.org/en/stable/settings.html

import os

# Debugging
loglevel = os.getenv('LOGLEVEL', 'warning')

# SSL encryption
keyfile = os.getenv('KEYFILE')
certfile = os.getenv('CERTFILE')

# Server socket
bind = list(os.getenv('BIND', '127.0.0.1:8000').split())

workers = int(os.getenv('WORKERS', 1))
threads = int(os.getenv('THREADS', 1))
