import os
import json
import time
from datetime import datetime
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
    main_bucket_name = os.environ.get("MAIN_BUCKET_NAME")

    if main_bucket_name is None:
        raise Exception("Bucket name not found")

    create_association_response = ssm.create_association(
        Name = "AWS-RunPatchBaseline",
        Parameters = {
            "Operation": ["Install"],
            "InstallOverrideList": ["s3://{}/InstallOverrideLists/{}.yml".format(main_bucket_name, instance_id)]
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

    # Stop the first invocation of the newly created association
    now = datetime.now()
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
    api_response = {
        "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
                }
    }

    try:
        request = json.loads(event['body'])

        if 'instanceId' not in request:
            raise Exception("instanceId not specified")
        
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

        api_response["statusCode"] = 200
        api_response["body"] = json.dumps(response)
    except Exception as e:
        api_response["statusCode"] = 400
        api_response["body"] = json.dumps({
            "message": str(e)
        })
    finally:
        return api_response