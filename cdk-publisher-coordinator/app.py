#!/usr/bin/env python3
import aws_cdk as cdk
from cdk_publisher_coordinator.cdk_publisher_coordinator_stack import CdkPublisherCoordinatorStack


app = cdk.App()
CdkPublisherCoordinatorStack(app, 
    "CdkPublisherCoordinatorStack",
    stack_name=app.node.try_get_context("stackName")
)

app.synth()
