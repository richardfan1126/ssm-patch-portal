#!/bin/bash

GREEN='\033[0;32m'
GREEN_BOLD='\033[1;32m'
NO_STYLE='\033[0m'

command -v python3 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "Please install python3 first"
    exit 1
fi

command -v pip3 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "Please install pip3 first"
    exit 1
fi

command -v cdk 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "Please install AWS CDK first"
    exit 1
fi

command -v jq 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "Please install jq first"
    exit 1
fi

command -v npm 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "Please install npm first"
    exit 1
fi

command -v npx 2>&1 1>/dev/null
if [[ $? -ne 0 ]]; then
    >&2 echo "Please install npx first"
    exit 1
fi

set -e

if [[ -f .env ]]; then
    source .env
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
echo -e "${GREEN}While waiting for frontend deployment. You can now create user in UserPool ${GREEN_BOLD}https://console.aws.amazon.com/cognito/users#/pool/${USERPOOL_ID}${GREEN} first.${NO_STYLE}"
read -p "Press Enter to continue"

# Generate amplify config file from CDK outputs
mv cdk-outputs.json custom-config.ts
cat custom-config.ts | jq 'first(.[])' > custom-config.ts
echo "export const customConfig = $(cat custom-config.ts);" > custom-config.ts
mv custom-config.ts frontend/src/custom-config.ts

# Build frontend webapp
cd frontend
npm install
npx -p @angular/cli ng build

# Deploy frontend CDK stack
cd ../frontend_stack
cdk deploy