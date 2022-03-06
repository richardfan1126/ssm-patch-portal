from doctest import run_docstring_examples
from aws_cdk import (
    NestedStack,
    RemovalPolicy,
    aws_lambda,
    aws_apigateway as apigateway,
    aws_iam as iam
)
import aws_cdk
from constructs import Construct

class ApiStack(NestedStack):
    api = None
    bucket_name = None
    bucket_arn = None

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        self.bucket_name = kwargs.pop('bucket_name')
        self.bucket_arn = kwargs.pop('bucket_arn')
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
                        "ssm:DescribeInstancePatchStates",
                    ],
                    resources = ["*"]
                ),
            ]
        )

        instance_query_function_role = instance_query_function.role
        instance_query_function_role.add_managed_policy(instance_query_function_policy)



        trigger_scan_association_function = aws_lambda.Function(
            self, "TriggerScanAssociationFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/trigger_scan_association/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(10),
            environment = {
                "MAIN_BUCKET_NAME": self.bucket_name
            }
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



        query_scan_status_function = aws_lambda.Function(
            self, "QueryScanStatusFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/query_scan_status/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(10),
            environment = {
                "MAIN_BUCKET_NAME": self.bucket_name
            }
        )

        query_scan_status_function_policy = iam.ManagedPolicy(
            self, "QueryScanStatusFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "ssm:ListAssociations",
                    ],
                    resources = ["*"]
                ),
            ]
        )

        query_scan_status_function_role = query_scan_status_function.role
        query_scan_status_function_role.add_managed_policy(query_scan_status_function_policy)



        get_instance_detail_function = aws_lambda.Function(
            self, "GetInstanceDetailFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/get_instance_detail/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(10),
        )

        get_instance_detail_function_policy = iam.ManagedPolicy(
            self, "GetInstanceDetailFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "ssm:DescribeInstancePatches",
                        "ssm:DescribeInstancePatchStates",
                        "ssm:ListAssociations",
                        "ec2:DescribeInstances",
                    ],
                    resources = ["*"]
                ),
            ]
        )

        get_instance_detail_function_role = get_instance_detail_function.role
        get_instance_detail_function_role.add_managed_policy(get_instance_detail_function_policy)


        start_patch_function_dependencies = aws_lambda.LayerVersion(
            self, "StartPatchFunctionDependencies",
            removal_policy = RemovalPolicy.DESTROY,
            compatible_runtimes = [aws_lambda.Runtime.PYTHON_3_8],
            code = aws_lambda.Code.from_asset('./api_stack/layer/start_patch/'),
        )

        start_patch_function = aws_lambda.Function(
            self, "StartPatchFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            layers = [start_patch_function_dependencies],
            code = aws_lambda.Code.from_asset('./api_stack/function/start_patch/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(10),
            environment = {
                "MAIN_BUCKET_NAME": self.bucket_name
            }
        )

        start_patch_function_policy = iam.ManagedPolicy(
            self, "StartPatchFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "s3:PutObject",
                        "s3:PutObjectAcl"
                    ],
                    resources = ["{}/*".format(self.bucket_arn)]
                ),
                iam.PolicyStatement(
                    actions = [
                        "ssm:DescribeAssociationExecutions",
                        "ssm:StartAssociationsOnce",
                        "ssm:ListAssociations",
                    ],
                    resources = ["*"]
                ),
                iam.PolicyStatement(
                    actions = [
                        "ssm:CreateAssociation",
                    ],
                    resources = [
                        "arn:aws:ssm:*:*:document/AWS-RunPatchBaseline",
                        "arn:aws:ec2:*:*:instance/*",
                    ]
                ),
            ]
        )

        start_patch_function_role = start_patch_function.role
        start_patch_function_role.add_managed_policy(start_patch_function_policy)

        api_method_options = {
            "authorization_type": apigateway.AuthorizationType.IAM,
        }

        api = apigateway.RestApi(
            self, "SsmPatchPortalAPI",
            default_cors_preflight_options = apigateway.CorsOptions(
                allow_origins = ['*'],
                allow_headers = [
                    'Authorization',
                    'Content-Type',
                    'X-Amz-Date',
                    'X-Amz-Security-Token',
                    'X-Api-Key'
                ],
                allow_methods = [
                    'DELETE',
                    'GET',
                    'HEAD',
                    'OPTIONS',
                    'PATCH',
                    'POST',
                    'PUT'
                ],
                status_code = 200
            ),
        )

        api_instances = api.root.add_resource('instances')
        api_instances.add_method('GET', apigateway.LambdaIntegration(instance_query_function), **api_method_options)

        api_association = api.root.add_resource('association')

        api_association_scan = api_association.add_resource('scan')
        api_association_scan.add_method('GET', apigateway.LambdaIntegration(query_scan_status_function), **api_method_options)
        api_association_scan.add_method('POST', apigateway.LambdaIntegration(trigger_scan_association_function), **api_method_options)

        api_missing_patch = api.root.add_resource('detail')
        api_missing_patch.add_method('GET', apigateway.LambdaIntegration(get_instance_detail_function), **api_method_options)

        api_patch = api.root.add_resource('patch')
        api_patch.add_method('POST', apigateway.LambdaIntegration(start_patch_function), **api_method_options)


        self.api = api
