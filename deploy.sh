#!/bin/bash

if [[ -f .env ]]; then
    source .env
fi

# Build Lambda layer
pip install -t api_stack/layer/start_patch/ -r api_stack/function/start_patch/requirements.txt

# Deploy CDK stack
cdk deploy --parameters $PARAMETERS