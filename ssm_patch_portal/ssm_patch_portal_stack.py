from aws_cdk import (
    Stack,
)
import aws_cdk
from constructs import Construct

from api_stack.api_stack import ApiStack
from cognito_stack.cognito_stack import CognitoStack
from s3_bucket_stack.s3_bucket_stack import S3BucketStack

class SsmPatchPortal(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ec2_iam_role_arns = aws_cdk.CfnParameter(
            self, "Ec2IamRoleArns",
            description = "A comma-delimited list of IAM role ARNs that are attached to target EC2 instances.\n" +
            "This is to grant EC2 instances permission to read the patch list from S3 bucket.",
        )

        s3_bucket_stack = S3BucketStack(self, "S3BucketStack",
            ec2_iam_role_arns = ec2_iam_role_arns
        )

        
        api_stack = ApiStack(self, "ApiStack",
            bucket_name = s3_bucket_stack.main_bucket.bucket_name,
            bucket_arn = s3_bucket_stack.main_bucket.bucket_arn
        )

        cognito_stack = CognitoStack(self, "CognitoStack",
            api_id = api_stack.api.rest_api_id
        )

        aws_cdk.CfnOutput(
            self, "ApiEndpoint",
            value = api_stack.api.url.rstrip("/")
        )

        aws_cdk.CfnOutput(
            self, "IdentityPoolId",
            value = cognito_stack.identity_pool.ref
        )

        aws_cdk.CfnOutput(
            self, "UserPoolId",
            value = cognito_stack.user_pool.user_pool_id
        )

        aws_cdk.CfnOutput(
            self, "UserPoolWebClientId",
            value = cognito_stack.user_pool_client.user_pool_client_id
        )
