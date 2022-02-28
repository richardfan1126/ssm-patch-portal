from email import policy
from aws_cdk import (
    NestedStack,
    aws_s3 as s3,
    aws_iam as iam
)
import aws_cdk
from constructs import Construct

class S3BucketStack(NestedStack):
    main_bucket = None
    ec2_iam_role_arns = None

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        self.ec2_iam_role_arns = kwargs.pop('ec2_iam_role_arns')
        super().__init__(scope, construct_id, **kwargs)

        self.main_bucket = s3.Bucket(
            self, "SsmPatchPortal",
            block_public_access = s3.BlockPublicAccess.BLOCK_ALL,
            encryption = s3.BucketEncryption.S3_MANAGED,
        )
        
        
        # Allow EC2 instance read access on the bucket        
        bucket_policy = iam.PolicyStatement(
            actions = ["s3:GetObject"],
            resources = [self.main_bucket.arn_for_objects("*")],
        )

        for principal in aws_cdk.Fn.split(",", self.ec2_iam_role_arns.value_as_string):
            bucket_policy.add_arn_principal(principal)

        self.main_bucket.add_to_resource_policy(bucket_policy)