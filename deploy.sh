#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
GREEN_BOLD='\033[1;32m'
NO_STYLE='\033[0m'

command -v python3 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "${RED}Please install python3 first${NO_STYLE}"
    exit 1
fi

command -v pip3 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "${RED}Please install pip3 first${NO_STYLE}"
    exit 1
fi

command -v cdk 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "${RED}Please install AWS CDK first${NO_STYLE}"
    exit 1
fi

command -v jq 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "${RED}Please install jq first${NO_STYLE}"
    exit 1
fi

command -v npm 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "${RED}Please install npm first${NO_STYLE}"
    exit 1
fi

command -v npx 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "${RED}Please install npx first${NO_STYLE}"
    exit 1
fi

set -e

if [[ -f .env ]]; then
    source .env
fi

if [[ -z $PARAMETERS ]]; then
    >&2 echo -e "${RED}Please specify the parameters in .env file\nUse .env.sample as example${NO_STYLE}"
    exit 1
fi

# Create virtualenv and install CDK dependencies
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Build Lambda layer
pip3 install -t api_stack/layer/start_patch/ -r api_stack/function/start_patch/requirements.txt

# Deploy Backend CDK stack
cdk deploy --parameters $PARAMETERS --outputs-file cdk-outputs.json

# Prompt user to create user while waiting for frontend deployment
USERPOOL_ID=$(cat cdk-outputs.json | jq -r 'first(.[]).UserPoolId')
echo -e "${GREEN}You can now create user in UserPool ${GREEN_BOLD}https://console.aws.amazon.com/cognito/users#/pool/${USERPOOL_ID}/users${NO_STYLE}"

# Ask user to continue deploying backend or exit
read -p "Continue to deploy frontend stack? (Y/n)" IS_CONTINUE
if [[ "${IS_CONTINUE}" == "n" ||  "${IS_CONTINUE}" == "N" ]]; then
    rm cdk-outputs.json
    exit 0
fi

# Generate amplify config file from CDK outputs
CUSTOM_CONFIG=$(cat cdk-outputs.json | jq 'first(.[])')
echo "export const customConfig = ${CUSTOM_CONFIG};" > frontend/src/custom-config.ts
rm cdk-outputs.json

# Build frontend webapp
cd frontend
npm install
npx -p @angular/cli ng build

# Deploy frontend CDK stack
cd ../frontend_stack
cdk deploy