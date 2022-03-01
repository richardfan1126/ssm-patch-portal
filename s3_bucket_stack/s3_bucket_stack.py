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
        
        
        # Allow EC2 instance read/write access on the bucket
        override_list_read_policy = iam.PolicyStatement(
            actions = ["s3:GetObject"],
            resources = [self.main_bucket.arn_for_objects("InstallOverrideLists/*")],
        )

        command_output_policy = iam.PolicyStatement(
            actions = [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            resources = [self.main_bucket.arn_for_objects("CommandOutputs/*")],
        )

        for principal in aws_cdk.Fn.split(",", self.ec2_iam_role_arns.value_as_string):
            override_list_read_policy.add_arn_principal(principal)
            command_output_policy.add_arn_principal(principal)

        self.main_bucket.add_to_resource_policy(override_list_read_policy)
        self.main_bucket.add_to_resource_policy(command_output_policy)