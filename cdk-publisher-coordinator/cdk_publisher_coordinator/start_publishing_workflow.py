from constructs import Construct
from aws_cdk import (
    aws_lambda
)

class StartPublishingWorkflow(Construct):
    @property
    def function(self):
        return self._func

    def __init__(self, scope: Construct, id: str, log_level: str, assets_per_revision: str, state_machine_arn: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        self._func = aws_lambda.Function(self,
            "StartPublishingWorkflow",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset("../source/StartPublishingWorkflowFunction"),
            handler="app.lambda_handler",
            environment={
                'STATE_MACHINE_ARN' : state_machine_arn,
                'LOG_LEVEL' : log_level,
                'ASSETS_PER_REVISION': assets_per_revision
            }
        )