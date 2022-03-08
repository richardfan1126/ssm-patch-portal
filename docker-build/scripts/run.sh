#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
GREEN_BOLD='\033[1;32m'
NO_STYLE='\033[0m'

set -e

cd /app

if [[ -f .env ]]; then
    source .env
fi

# Check if parameters are set
if [[ -z $Ec2IamRoleArns ]]; then
    >&2 echo -e "${RED}Please specify the Ec2IamRoleArns in .env file\nUse .env.sample as example${NO_STYLE}"
    exit 1
fi

if [[ -z $AdminEmail ]]; then
    >&2 echo -e "${RED}Please specify the AdminEmail in .env file\nUse .env.sample as example${NO_STYLE}"
    exit 1
fi

# Create virtualenv and install CDK dependencies
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

# Build Lambda layer
pip3 install -t api_stack/layer/start_patch/ -r api_stack/function/start_patch/requirements.txt

# Deploy Backend CDK stack
cdk deploy --parameters Ec2IamRoleArns=$Ec2IamRoleArns --parameters AdminEmail=$AdminEmail --outputs-file cdk-outputs.json

# Ask user to continue deploying backend or exit
read -p "Continue to deploy frontend stack? (Y/n) " IS_CONTINUE
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
npm_config_unsafe_perm=true npx -p @angular/cli ng build

# Deploy frontend CDK stack
cd ../frontend_stack
cdk deploy --require-approval never
