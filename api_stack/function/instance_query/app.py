import json
import boto3

def handler(event, context):
    ec2 = boto3.client('ec2')
    ssm = boto3.client('ssm')

    ec2_names = {}
    next_token = None
    first_run = True

    while next_token is not None or first_run:
        first_run = False

        request_args = {
            "MaxResults": 1000
        }

        if next_token is not None:
            request_args["NextToken"] = next_token

        ec2_response = ec2.describe_instances(**request_args)

        for reservation in ec2_response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']

                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        ec2_names[instance_id] = tag['Value']
        
        if 'NextToken' in ec2_response:
            next_token = ec2_response['NextToken']
        else:
            next_token = None

    patch_associations = {}
    next_token = None
    first_run = True

    while next_token is not None or first_run:
        first_run = False

        request_args = {
            "AssociationFilterList": [
                {
                    "key": "Name",
                    "value": "AWS-RunPatchBaseline"
                }
            ],
            "MaxResults": 50
        }

        if next_token is not None:
            request_args["NextToken"] = next_token

        patch_association_response = ssm.list_associations(**request_args)

        for association in patch_association_response['Associations']:
            association_name = association['AssociationName']

            if not association_name.startswith("ssm-patch-portal-"):
                continue
            
            instance_id = None
            for target in association['Targets']:
                if target['Key'] == 'InstanceIds':
                    instance_id = target['Values'][0]
                    break

            if instance_id is None:
                continue

            patch_associations[instance_id] = {
                "associationId": association["AssociationId"] if "AssociationId" in association else "",
                "overview": association["Overview"] if "Overview" in association else "",
                "lastExecutionDate": association["LastExecutionDate"].strftime("%Y-%m-%dT%H:%M:%SZ") if "LastExecutionDate" in association else "",
            }
        
        if 'NextToken' in patch_association_response:
            next_token = patch_association_response['NextToken']
        else:
            next_token = None
        
    instances = []
    next_token = None
    first_run = True

    while next_token is not None or first_run:
        first_run = False

        request_args = {
            "InstanceInformationFilterList": [
                {
                    'key': 'ResourceType',
                    'valueSet': ['EC2Instance']
                }
            ],
            "MaxResults": 50
        }

        if next_token is not None:
            request_args["NextToken"] = next_token

        ssm_instace_response = ssm.describe_instance_information(**request_args)

        for instance in ssm_instace_response['InstanceInformationList']:
            instance_id = instance['InstanceId']

            item = {
                'instanceId': instance_id,
                'name': ec2_names[instance_id] if instance_id in ec2_names else '',
                'platformType': instance['PlatformType'] if 'PlatformType' in instance else '',
                'platformName': instance['PlatformName'] if 'PlatformName' in instance else '',
                'patchAssociation': patch_associations[instance_id] if instance_id in patch_associations else {},
            }
            
            instances.append(item)
        
        if 'NextToken' in ssm_instace_response:
            next_token = ssm_instace_response['NextToken']
        else:
            next_token = None

    return {
        "statusCode": 200,
        "body": json.dumps(instances)
    }