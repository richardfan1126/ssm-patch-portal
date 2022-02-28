from doctest import run_docstring_examples
from aws_cdk import (
    NestedStack,
    aws_lambda,
    aws_apigateway as apigateway,
    aws_iam as iam
)
import aws_cdk
from constructs import Construct

class ApiStack(NestedStack):
    api_endpoint = None
    bucket_name = None

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        self.bucket_name = kwargs.pop('bucket_name')
        super().__init__(scope, construct_id, **kwargs)

        instance_query_function = aws_lambda.Function(
            self, "InstanceQueryFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/instance_query/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(10),
        )

        instance_query_function_policy = iam.ManagedPolicy(
            self, "InstanceQueryFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "ec2:DescribeInstances",
                        "ssm:DescribeInstanceInformation",
                        "ssm:ListAssociations",
                    ],
                    resources = ["*"]
                ),
            ]
        )

        instance_query_function_role = instance_query_function.role
        instance_query_function_role.add_managed_policy(instance_query_function_policy)



        create_patch_association_function = aws_lambda.Function(
            self, "CreatePatchAssociationFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/create_patch_association/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(30),
            environment = {
                "MAIN_BUCKET_NAME": self.bucket_name
            }
        )

        create_patch_association_function_policy = iam.ManagedPolicy(
            self, "CreatePatchAssociationFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "ssm:CreateAssociation",
                    ],
                    resources = [
                        "arn:aws:ssm:*:*:document/AWS-RunPatchBaseline",
                        "arn:aws:ec2:*:*:instance/*",
                    ]
                ),
                iam.PolicyStatement(
                    actions = [
                        "ssm:ListCommands",
                        "ssm:CancelCommand",
                        "ssm:ListAssociations",
                    ],
                    resources = ["*"]
                ),
            ]
        )

        create_patch_association_function_role = create_patch_association_function.role
        create_patch_association_function_role.add_managed_policy(create_patch_association_function_policy)



        trigger_scan_association_function = aws_lambda.Function(
            self, "TriggerScanAssociationFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/trigger_scan_association/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(30),
        )

        trigger_scan_association_function_policy = iam.ManagedPolicy(
            self, "TriggerScanAssociationFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "ssm:CreateAssociation",
                    ],
                    resources = [
                        "arn:aws:ssm:*:*:document/AWS-RunPatchBaseline",
                        "arn:aws:ssm:*:*:managed-instance/*",
                        "arn:aws:ec2:*:*:instance/*",
                    ]
                ),
                iam.PolicyStatement(
                    actions = [
                        "ssm:ListAssociations",
                        "ssm:StartAssociationsOnce",
                    ],
                    resources = ["*"]
                ),
            ]
        )

        trigger_scan_association_function_role = trigger_scan_association_function.role
        trigger_scan_association_function_role.add_managed_policy(trigger_scan_association_function_policy)



        query_missing_patch_function = aws_lambda.Function(
            self, "QueryMissingPatchFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/query_missing_patch/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(30),
        )

        query_missing_patch_function_policy = iam.ManagedPolicy(
            self, "QueryMissingPatchFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "ssm:DescribeInstancePatches",
                    ],
                    resources = ["*"]
                ),
            ]
        )

        query_missing_patch_function_role = query_missing_patch_function.role
        query_missing_patch_function_role.add_managed_policy(query_missing_patch_function_policy)



        api = apigateway.RestApi(
            self, "API",
        )

        api_instances = api.root.add_resource('instances')
        api_instances.add_method('GET', apigateway.LambdaIntegration(instance_query_function))

        api_association = api.root.add_resource('association')

        api_association_patch = api_association.add_resource('patch')
        api_association_patch.add_method('POST', apigateway.LambdaIntegration(create_patch_association_function))
        
        api_association_scan = api_association.add_resource('scan')
        api_association_scan.add_method('POST', apigateway.LambdaIntegration(trigger_scan_association_function))

        api_missing_patch = api.root.add_resource('missing-patch')
        api_missing_patch.add_method('GET', apigateway.LambdaIntegration(query_missing_patch_function))


        self.api_endpoint = api.url