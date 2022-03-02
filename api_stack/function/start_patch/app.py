import sys
sys.path.append('/opt')

import time
from datetime import datetime, timedelta
import os
import json
import boto3
import yaml

s3 = boto3.client('s3')
ssm = boto3.client('ssm')

def export_override_list(instance_id, patches):
    bucket_name = os.environ.get('MAIN_BUCKET_NAME')

    patches_list = []
    for patch in patches:
        if 'KBId' not in patch or 'Title' not in patch:
            raise Exception("KBId or Title is missing")

        patches_list.append(
            {
                'id': patch.get('KBId'),
                'title': patch.get('Title'),
            }
        )
    
    if len(patches_list) == 0:
        raise Exception("There must be at least 1 patch to apply")
    
    file_name = "{}.yml".format(instance_id)

    with open("/tmp/{}".format(file_name), 'w') as f:
        yaml.dump({'patches': patches_list}, f, default_flow_style=False)
    
    s3.upload_file(
        "/tmp/{}".format(file_name),
        bucket_name,
        "InstallOverrideLists/{}".format(file_name)
    )

# Check if association linked to the correct instance
def check_association(instance_id, association_id):
    get_association_response = ssm.describe_association(
        AssociationId = association_id,
    )
    
    for target in get_association_response['AssociationDescription']['Targets']:
        if target['Key'] == 'InstanceIds' and len(target['Values']) == 1 and target['Values'][0] == instance_id:
            return True
    
    return False

def apply_association(association_id):
    now = datetime.now() - timedelta(seconds = 5)
    now_string = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    ssm.start_associations_once(
        AssociationIds=[association_id]
    )

    # Get the execution detail
    retry_count = 0
    while retry_count < 5:
        association_execution_response = ssm.describe_association_executions(
            AssociationId = association_id,
            Filters=[
                {
                    'Key': 'CreatedTime',
                    'Type': 'GREATER_THAN',
                    'Value': now_string,
                },
            ],
        )

        if len(association_execution_response['AssociationExecutions']) > 0:
            return association_execution_response['AssociationExecutions'][0]

        retry_count += 1
        time.sleep(1)
    
    return None

def handler(event, context):
    api_response = {
        "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
                }
    }

    try:
        if event['body'] is None:
            raise Exception("Request body should not be empty")

        request = json.loads(event['body'])

        if 'instanceId' not in request:
            raise Exception("instanceId not specified")

        if 'associationId' not in request:
            raise Exception("associationId not specified")

        if 'patches' not in request:
            raise Exception("patches not specified")

        if type(request['patches']) != list:
            raise Exception("patches must be a list")

        instance_id = request['instanceId']
        association_id = request['associationId']
        patches = request['patches']

        if not check_association(instance_id, association_id):
            raise Exception("associationId and instanceId do not match")

        export_override_list(instance_id, patches)
        execution = apply_association(association_id)

        if execution is None:
            raise Exception("Failed to get execution detail")

        execution['CreatedTime'] = execution['CreatedTime'].strftime("%Y-%m-%dT%H:%M:%SZ") if 'CreatedTime' in execution and execution['CreatedTime'] is not None else ""
        execution['LastExecutionDate'] = execution['LastExecutionDate'].strftime("%Y-%m-%dT%H:%M:%SZ") if 'LastExecutionDate' in execution and execution['LastExecutionDate'] is not None else ""
        
        api_response["statusCode"] = 200
        api_response["body"] = json.dumps(execution)
    except Exception as e:
        api_response["statusCode"] = 400
        api_response["body"] = json.dumps({
            "message": str(e)
        })
    finally:
        return api_response