#!/bin/bash

RED='\033[0;31m'
NO_STYLE='\033[0m'

command -v docker 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo -e "${RED}Please install docker first${NO_STYLE}"
    exit 1
fi

set -e

if [[ ! -f ../.env ]]; then
    >&2 echo -e "${RED}Please specify the parameters in .env file\nUse .env.sample as example${NO_STYLE}"
    exit 1
fi

read -p "Please specify the location of AWS credential [~/.aws] " AWS_CREDENTIAL_DIR

if [[ -z $AWS_CREDENTIAL_DIR ]]; then
    AWS_CREDENTIAL_DIR=~/.aws
fi

docker build -f Dockerfile -t ssm-patch-portal-build ..
docker run --volume $AWS_CREDENTIAL_DIR:/root/.aws/:ro -it ssm-patch-portal-build