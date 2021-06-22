FROM python:3.9-slim

# Build arguments
ARG username=ansible

RUN apt update && apt upgrade -y && apt install -y openssh-client &&\
  pip install ansible==4.1.*

# Non-root user
RUN groupadd -r $username && useradd -rm -g $username $username
USER $username

ENTRYPOINT ["ansible"]
