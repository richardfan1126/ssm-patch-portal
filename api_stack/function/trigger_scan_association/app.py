import os

import json
import boto3

ssm = boto3.client('ssm')

def query_association():
    query_association_response = ssm.list_associations(
        AssociationFilterList = [
            {
                "key": "AssociationName",
                "value": "ssm-patch-portal-scan"
            }
        ],
    )

    if len(query_association_response['Associations']) > 0:
        return query_association_response['Associations'][0]
    else:
        return None

def create_association():
    main_bucket_name = os.environ.get("MAIN_BUCKET_NAME")

    create_association_response = ssm.create_association(
        Name = "AWS-RunPatchBaseline",
        Parameters = {
            "Operation": ["Scan"],
        },
        Targets = [
            {
                "Key": "InstanceIds",
                "Values": ["*"]
            }
        ],
        AssociationName = "ssm-patch-portal-scan",
        OutputLocation = {
            'S3Location': {
                'OutputS3BucketName': main_bucket_name,
                'OutputS3KeyPrefix': "CommandOutputs/" 
            }
        },
    )

    return create_association_response

def handler(event, context):
    api_response = {
        "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
                }
    }

    try:
        # Check if patch scan association already exist
        query_association_response = query_association()

        if query_association_response is None:
            # Create a new association if none exist
            create_association_response = create_association()
            association = create_association_response["AssociationDescription"]
        else:
            association = query_association_response
            association_id = association['AssociationId']

            # Trigger re-scan
            ssm.start_associations_once(
                AssociationIds=[association_id]
            )
        
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