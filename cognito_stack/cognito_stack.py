from aws_cdk import (
    NestedStack,
    RemovalPolicy,
    Stack,
    aws_cognito as cognito,
    aws_iam as iam,
)
import aws_cdk
from constructs import Construct

class CognitoStack(NestedStack):
    user_pool = None
    user_pool_client = None
    identity_pool = None
    api_id = None

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        self.api_id = kwargs.pop('api_id')
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = cognito.UserPool(
            self, "UserPool",
            auto_verify = {
                "email": True
            },
            self_sign_up_enabled = False,
            sign_in_aliases = {
                "email": True,
                "username": True
            },
            standard_attributes = {
                "email": {
                    "required": True
                }
            },
            removal_policy = RemovalPolicy.DESTROY,
        )

        self.user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool = self.user_pool,
            generate_secret = False,
            refresh_token_validity = aws_cdk.Duration.days(1),
        )

        self.identity_pool = cognito.CfnIdentityPool(
            self, "IdentityPool",
            allow_unauthenticated_identities = False,
            cognito_identity_providers = [
                {
                    "clientId": self.user_pool_client.user_pool_client_id,
                    "providerName": self.user_pool.user_pool_provider_name
                }
            ]
        )

        api_prod_execute_arn = Stack.of(self).format_arn(
            service = 'execute-api',
            resource = self.api_id,
            resource_name = 'prod/*'
        )

        cognito_authorized_role = iam.Role(
            self, "AuthorizedRole",
            assumed_by = iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com',
                {
                    "StringEquals": { 'cognito-identity.amazonaws.com:aud': self.identity_pool.ref },
                    'ForAnyValue:StringLike': { 'cognito-identity.amazonaws.com:amr': 'authenticated' }
                },
                'sts:AssumeRoleWithWebIdentity'
            ),
            inline_policies = {
                'InvokeApiPolicy': iam.PolicyDocument(
                    statements = [
                        iam.PolicyStatement(
                            actions = ['execute-api:Invoke'],
                            resources = [
                                api_prod_execute_arn
                            ]
                        )
                    ]
                )
            }
        )

        identity_pool_role_attachment = cognito.CfnIdentityPoolRoleAttachment(
            self, "IdentityPoolRoleAttachment",
            identity_pool_id = self.identity_pool.ref,
            roles = {
                'authenticated': cognito_authorized_role.role_arn
            }
        )