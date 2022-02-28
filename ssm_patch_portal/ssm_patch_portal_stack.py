from aws_cdk import (
    Stack,
)
import aws_cdk
from constructs import Construct

from api_stack.api_stack import ApiStack

class SsmPatchPortalStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api_stack = ApiStack(self, "ApiStack")

        aws_cdk.CfnOutput(
            self, "QueryApiEndpoint",
            value = api_stack.api_endpoint
        )
