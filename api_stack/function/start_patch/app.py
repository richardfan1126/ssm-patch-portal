import sys
sys.path.append('/opt')

import os
import json
import boto3
import yaml

s3 = boto3.client('s3')

def export_override_list(instance_id, patches):
    bucket_name = os.environ.get('MAIN_BUCKET_NAME')

    patches_list = []
    for patch in patches:
        patches_list.append(
            {
                'id': patch.get('KBId'),
                'title': patch.get('Title'),
                'severity': patch.get('Severity')
            }
        )
    
    file_name = "{}.yml".format(instance_id)

    with open("/tmp/{}".format(file_name), 'w') as f:
        yaml.dump({'patches': patches_list}, f, default_flow_style=False)
    
    s3.upload_file(
        "/tmp/{}".format(file_name),
        bucket_name,
        "InstallOverrideLists/{}".format(file_name)
    )
    pass

def handler(event, context):
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

        return {
            "statusCode": 200,
            "body": json.dumps(request)
        }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": str(e)
        }