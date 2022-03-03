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

def handler(event, context):
    api_response = {
        "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept"
                }
    }

    try:
        query_association_response = query_association()

        if query_association_response is None:
            response = None
        else:
            association = query_association_response
        
            response = {
                "associationId": association["AssociationId"] if "AssociationId" in association else None,
                "lastExecutionDate": association["LastExecutionDate"].strftime("%Y-%m-%dT%H:%M:%SZ") if "LastExecutionDate" in association else None,
                "overview": association["Overview"] if "Overview" in association else None,
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