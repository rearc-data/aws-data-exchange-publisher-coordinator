#!/usr/bin/env python3
import aws_cdk as cdk

from cdk_publisher_coordinator.cdk_publisher_coordinator_stack import CdkPublisherCoordinatorStack


app = cdk.App()
CdkPublisherCoordinatorStack(app, "CdkPublisherCoordinatorStack")

app.synth()
