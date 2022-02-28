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

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
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
                        "ssm:DescribeInstanceInformation"
                    ],
                    resources = ["*"]
                )
            ]
        )

        instance_query_function_role = instance_query_function.role
        instance_query_function_role.add_managed_policy(instance_query_function_policy)



        create_association_function = aws_lambda.Function(
            self, "CreateAssociationFunction",
            runtime = aws_lambda.Runtime.PYTHON_3_8,
            code = aws_lambda.Code.from_asset('./api_stack/function/create_association/'),
            handler = 'app.handler',
            timeout = aws_cdk.Duration.seconds(10),
        )

        create_association_function_policy = iam.ManagedPolicy(
            self, "CreateAssociationFunctionPolicy",
            statements = [
                iam.PolicyStatement(
                    actions = [
                        "ssm:CreateAssociation",
                    ],
                    resources = [
                        "arn:aws:ssm:*:*:document/AWS-RunPatchBaseline",
                        "arn:aws:ec2:*:*:instance/*",
                    ]
                )
            ]
        )

        create_association_function_role = create_association_function.role
        create_association_function_role.add_managed_policy(create_association_function_policy)



        api = apigateway.RestApi(
            self, "API",
        )

        api_instances = api.root.add_resource('instances')
        api_instances.add_method('GET', apigateway.LambdaIntegration(instance_query_function))

        api_association = api.root.add_resource('association')
        api_association.add_method('POST', apigateway.LambdaIntegration(create_association_function))


        self.api_endpoint = api.url
