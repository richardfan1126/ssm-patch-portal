import json
import boto3

def create_association(instance_id):
    ssm = boto3.client('ssm')

    response = ssm.create_association(
        Name = "AWS-RunPatchBaseline",
        Parameters = {
            "Operation": ["Scan"],
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
        AssociationName = "{}-patch-scan".format(instance_id),
    )

    return response

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
        "body": response
    }