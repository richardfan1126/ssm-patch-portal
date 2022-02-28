import json
import time
from datetime import date
import boto3

def create_association(instance_id):
    ssm = boto3.client('ssm')

    create_association_response = ssm.create_association(
        Name = "AWS-RunPatchBaseline",
        Parameters = {
            "Operation": ["Install"],
        },
        Targets = [
            {
                "Key": "InstanceIds",
                "Values": [
                    instance_id
                ]
            }
        ],
        AssociationName = "ssm-patch-portal-{}".format(instance_id),
    )

    # Stop the first invocation of the newly created association
    now = date.today()
    now_string = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    retry_time = 0

    while retry_time < 10:
        try:
            if 'AssociationDescription' in create_association_response and 'AssociationId' in create_association_response['AssociationDescription']:
                association_id = create_association_response['AssociationDescription']['AssociationId']

                command_response = ssm.list_commands(
                    Filters = [
                        {
                            "key": "DocumentName",
                            "value": "AWS-RunPatchBaseline"
                        },
                        {
                            "key": "InvokedAfter",
                            "value": now_string
                        }
                    ]
                )

                for command in command_response['Commands']:
                    comment = command['Comment']

                    if comment.startswith(association_id):
                        command_id = command['CommandId']

                        ssm.cancel_command(
                            CommandId = command_id,
                        )
        finally:
            pass
        
        retry_time += 1
        time.sleep(1)

    return create_association_response

def handler(event, context):
    request = json.loads(event['body'])

    if 'instanceId' not in request:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "instanceId not specified"
            })
        }
    
    response = create_association(request['instanceId'])

    return {
        "statusCode": 200,
        "body": ""
    }