import json
from unittest.mock import patch
import boto3

ec2 = boto3.client('ec2')
ssm = boto3.client('ssm')

def get_instance_name(instance_id):
    ec2_response = ec2.describe_instances(
        InstanceIds=[instance_id],
    )

    if len(ec2_response['Reservations']) > 0 and len(ec2_response['Reservations'][0]['Instances']) > 0:
        instance = ec2_response['Reservations'][0]['Instances'][0]
    else:
        return None

    for tag in instance['Tags']:
        if tag['Key'] == 'Name':
            return tag['Value']

    return None

def get_missing_patches(instance_id):
    patches = []
    next_token = None
    first_run = True

    while next_token is not None or first_run:
        first_run = False

        request_args = {
            "InstanceId": instance_id,
            "Filters": [
                {
                    'Key': 'State',
                    'Values': [
                        'Missing',
                        'Failed',
                    ]
                },
            ],
            "MaxResults": 50
        }

        if next_token is not None:
            request_args["NextToken"] = next_token

        ssm_patch_response = ssm.describe_instance_patches(**request_args)

        for patch in ssm_patch_response['Patches']:
            item = patch
            item['InstalledTime'] = item['InstalledTime'].strftime("%Y-%m-%dT%H:%M:%SZ")

            patches.append(item)
        
        if 'NextToken' in ssm_patch_response:
            next_token = ssm_patch_response['NextToken']
        else:
            next_token = None
    
    return patches

def get_patch_association(instance_id):
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

def handler(event, context):
    api_response = {
        "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
                }
    }

    try:
        if event['queryStringParameters'] is None or 'instance-id' not in event['queryStringParameters']:
            raise Exception("instance-id not specified")
        
        instance_id = event['queryStringParameters']['instance-id']

        instance_name = get_instance_name(instance_id)
        missing_patches = get_missing_patches(instance_id)
        patch_association = get_patch_association(instance_id)

        is_patching = False
        if patch_association is not None and 'Overview' in patch_association and patch_association['Overview']['Status'] == "Pending":
            is_patching = True

        api_response["statusCode"] = 200
        api_response["body"] = json.dumps({
            "instanceName": instance_name,
            "isPatching": is_patching,
            "missingPatchCount": len(missing_patches),
            "missingPatches": missing_patches
        })
    except Exception as e:
        api_response["statusCode"] = 400
        api_response["body"] = json.dumps({
            "message": str(e)
        })
    finally:
        return api_response