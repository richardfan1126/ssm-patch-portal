from aws_cdk import (
    Stack,
)
import aws_cdk
from constructs import Construct

from api_stack.api_stack import ApiStack
from s3_bucket_stack.s3_bucket_stack import S3BucketStack

class SsmPatchPortal(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ec2_iam_role_arns = aws_cdk.CfnParameter(
            self, "Ec2IamRoleArns",
        )

        s3_bucket_stack = S3BucketStack(self, "S3BucketStack",
            ec2_iam_role_arns = ec2_iam_role_arns
        )
        api_stack = ApiStack(self, "ApiStack",
            bucket_name = s3_bucket_stack.main_bucket.bucket_name
        )

        aws_cdk.CfnOutput(
            self, "QueryApiEndpoint",
            value = api_stack.api_endpoint
        )
