import json
import time
from datetime import date
import boto3

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
    
    instance_id = request['instanceId']

    # Check if patch association already exist
    query_association_response = query_association(instance_id)

    if query_association_response is None:
        # Create a new association if none exist
        create_association_response = create_association(instance_id)
        association = create_association_response["AssociationDescription"]
    else:
        association = query_association_response
    
    response = {
        "associationId": association["AssociationId"] if "AssociationId" in association else ""
    }

    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }