import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_publisher_coordinator.cdk_publisher_coordinator_stack import CdkPublisherCoordinatorStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_publisher_coordinator/cdk_publisher_coordinator_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkPublisherCoordinatorStack(app, "cdk-publisher-coordinator")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
