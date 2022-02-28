import json
import boto3

def handler(event, context):
    ec2 = boto3.client('ec2')
    ssm = boto3.client('ssm')

    ec2_response = ec2.describe_instances()

    ec2_names = {}
    for reservation in ec2_response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']

            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    ec2_names[instance_id] = tag['Value']

    ssm_response = ssm.describe_instance_information(
        InstanceInformationFilterList = [
            {
                'key': 'ResourceType',
                'valueSet': ['EC2Instance']
            }
        ]
    )

    instances = []
    for instance in ssm_response['InstanceInformationList']:
        instance_id = instance['InstanceId']

        item = {
            'instanceId': instance_id,
            'name': ec2_names[instance_id] if instance_id in ec2_names else '',
            'platformType': instance['PlatformType'] if 'PlatformType' in instance else '',
            'platformName': instance['PlatformName'] if 'PlatformName' in instance else '',
        }
        
        instances.append(item)

    return {
        "statusCode": 200,
        "body": json.dumps(instances)
    }