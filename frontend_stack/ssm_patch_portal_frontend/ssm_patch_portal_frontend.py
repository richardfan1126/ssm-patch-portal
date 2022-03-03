from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
)
import aws_cdk
from constructs import Construct

class SsmPatchPortalFrontend(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(
            self, "SsmPatchPortalFrontend",
            block_public_access = s3.BlockPublicAccess.BLOCK_ALL,
            encryption = s3.BucketEncryption.S3_MANAGED,

        )

        s3_deployment.BucketDeployment(
            self, "SsmPatchPortalFrontendDeployment",
            destination_bucket = bucket,
            sources = [
                s3_deployment.Source.asset("../frontend/dist/ssm-patch-portal-frontend/"),
            ]
        )

        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "SsmPatchPortalAccessId",
        )

        cloudfront_dist = cloudfront.Distribution(
            self, "SsmPatchPortalCFDistribution",
            default_root_object = "index.html",
            default_behavior = {
                "origin": cloudfront_origins.S3Origin(bucket, origin_access_identity = origin_access_identity)
            }
        )

        aws_cdk.CfnOutput(
            self, "Portal_URL",
            value = "https://" + cloudfront_dist.domain_name
        )
