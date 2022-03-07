## Script to build richardfan1126/ssm-patch-portal-build-base
# FROM ubuntu:latest

# ENV DEBIAN_FRONTEND=noninteractive
# ENV TZ=Etc/UTC
# ENV NG_CLI_ANALYTICS=false

# RUN apt update && apt install -y curl
# RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
# RUN apt install -y python3 python3-pip python3-venv nodejs jq

# RUN npm install -g aws-cdk

##################################

## Use pre-built image base
FROM richardfan1126/ssm-patch-portal-build-base

COPY . /app
RUN chmod +x /app/docker-build/scripts/run.sh

WORKDIR /app
CMD ["/bin/bash", "-c", "/app/docker-build/scripts/run.sh"]
