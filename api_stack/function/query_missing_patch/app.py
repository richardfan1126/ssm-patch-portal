import json
import boto3

def handler(event, context):
    try:
        if event['queryStringParameters'] is None or 'instance-id' not in event['queryStringParameters']:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "instance-id not specified"
                })
            }
        
        instance_id = event['queryStringParameters']['instance-id']
        
        ssm = boto3.client('ssm')

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

        return {
            "statusCode": 200,
            "body": json.dumps({
                "count": len(patches),
                "patches": patches
            })
        }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": str(e)
            })
        }