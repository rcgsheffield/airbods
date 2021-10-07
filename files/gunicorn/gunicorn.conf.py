# Gunicorn configuration file
# https://docs.gunicorn.org/en/latest/configure.html#configuration-file

# Available settings:
# https://docs.gunicorn.org/en/stable/settings.html

# Debugging
# loglevel = 'debug'

# SSL
keyfile = '/home/www-data/airbods_shef_ac_uk.key'
certfile = '/home/www-data/airbods_shef_ac_uk_cert.cer'

# Server socket
bind = ['0.0.0.0:443']
