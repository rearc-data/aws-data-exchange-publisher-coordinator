from constructs import Construct
from aws_cdk import (
    aws_lambda,
    aws_iam,
    aws_stepfunctions_tasks,
    aws_stepfunctions
)

class CheckJobStatus(Construct):
    @property
    def function(self):
        return self._func
    @property
    def task(self):
        return self._task

    def __init__(self, scope: Construct, id: str, log_level: str , role: aws_iam.IManagedPolicy, **kwargs):
        super().__init__(scope, id, **kwargs)
        check_job_status_role = aws_iam.Role(self, 
            "CheckJobStatusRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[role]
        )
        check_job_status_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=["dataexchange:GetJob"],
                resources=["*"]
            )
        )
        self._func = aws_lambda.Function(self,
            "CheckJobStatus",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset("../source/CheckJobStatusFunction"),
            handler="app.lambda_handler",
            role=check_job_status_role,
            environment={
                'LOG_LEVEL' : log_level
            }
        )
        self._task = aws_stepfunctions_tasks.LambdaInvoke(self,
            "CheckJobStatusTask",
            lambda_function=self._func,
            input_path=aws_stepfunctions.JsonPath.string_at("$.Payload")
        )