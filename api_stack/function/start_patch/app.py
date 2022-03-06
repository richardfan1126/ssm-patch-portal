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

def query_association(instance_id):
    query_association_response = ssm.list_associations(
        AssociationFilterList = [
            {
                "key": "AssociationName",
                "value": "ssm-patch-portal-{}".format(instance_id),
            }
        ],
    )

    if len(query_association_response['Associations']) > 0:
        return query_association_response['Associations'][0]
    else:
        return None

def create_association(instance_id):
    main_bucket_name = os.environ.get("MAIN_BUCKET_NAME")

    if main_bucket_name is None:
        raise Exception("Bucket name not found")

    create_association_response = ssm.create_association(
        Name = "AWS-RunPatchBaseline",
        Parameters = {
            "Operation": ["Install"],
            "InstallOverrideList": ["s3://{}/InstallOverrideLists/{}.yml".format(main_bucket_name, instance_id)],
            "RebootOption": ["NoReboot"],
        },
        Targets = [
            {
                "Key": "InstanceIds",
                "Values": [
                    instance_id
                ]
            }
        ],
        OutputLocation = {
            'S3Location': {
                'OutputS3BucketName': main_bucket_name,
                'OutputS3KeyPrefix': "CommandOutputs/" 
            }
        },
        MaxConcurrency = "1",
        AssociationName = "ssm-patch-portal-{}".format(instance_id),
    )

    return create_association_response

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

        if 'patches' not in request:
            raise Exception("patches not specified")

        if type(request['patches']) != list:
            raise Exception("patches must be a list")

        instance_id = request['instanceId']
        patches = request['patches']

        export_override_list(instance_id, patches)

        # Check if patch association already exist
        query_association_response = query_association(instance_id)

        if query_association_response is None:
            # Create a new association if none exist (No need to trigger as new association will be executed automatically)
            create_association_response = create_association(instance_id)
            association = create_association_response["AssociationDescription"]
        else:
            association = query_association_response
            
            # Trigger the association if already exist
            association_id = association['AssociationId']
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