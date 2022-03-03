import json
import boto3

def handler(event, context):
    api_response = {
        "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
                }
    }

    try:
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
            
        instances = {}
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
                    'patchState': None,
                }
                
                instances[instance_id] = item
            
            if 'NextToken' in ssm_instace_response:
                next_token = ssm_instace_response['NextToken']
            else:
                next_token = None
        
        next_token = None
        first_run = True

        while next_token is not None or first_run:
            first_run = False

            request_args = {
                "InstanceIds": list(instances.keys()),
                "MaxResults": 50
            }

            if next_token is not None:
                request_args["NextToken"] = next_token

            patch_states_response = ssm.describe_instance_patch_states(**request_args)

            for patch_state in patch_states_response['InstancePatchStates']:
                instance_id = patch_state['InstanceId']

                if instance_id in instances:
                    instances[instance_id]['patchState'] = {
                        'InstalledCount': patch_state['InstalledCount'] if 'InstalledCount' in patch_state else None,
                        'InstalledPendingRebootCount': patch_state['InstalledPendingRebootCount'] if 'InstalledPendingRebootCount' in patch_state else None,
                        'MissingCount': patch_state['MissingCount'] if 'MissingCount' in patch_state else None,
                        'FailedCount': patch_state['FailedCount'] if 'FailedCount' in patch_state else None,
                    }
            
            if 'NextToken' in patch_states_response:
                next_token = patch_states_response['NextToken']
            else:
                next_token = None

        
        api_response["statusCode"] = 200
        api_response["body"] = json.dumps(list(instances.values()))
    except Exception as e:
        api_response["statusCode"] = 400
        api_response["body"] = json.dumps({
            "message": str(e)
        })
    finally:
        return api_response