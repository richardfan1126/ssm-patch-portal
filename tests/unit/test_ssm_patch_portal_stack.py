import aws_cdk as core
import aws_cdk.assertions as assertions

from ssm_patch_portal.ssm_patch_portal_stack import SsmPatchPortal

# example tests. To run these tests, uncomment this file along with the example
# resource in ssm_patch_portal/ssm_patch_portal_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SsmPatchPortal(app, "ssm-patch-portal")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
