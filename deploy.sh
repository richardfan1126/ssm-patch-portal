#!/bin/bash

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

set -e

if [[ -f .env ]]; then
    source .env
fi

# Build Lambda layer
pip3 install -t api_stack/layer/start_patch/ -r api_stack/function/start_patch/requirements.txt

# Deploy CDK stack
cdk deploy --parameters $PARAMETERS --outputs-file custom-config.ts

# Generate amplify config file from CDK outputs
cat custom-config.ts | jq 'first(.[])' > custom-config.ts
echo "export const customConfig = $(cat custom-config.ts);" > custom-config.ts