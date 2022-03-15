from constructs import Construct
from aws_cdk import (
    aws_lambda,
    Fn,
    aws_stepfunctions_tasks
)

class PrepareRevisionInputMap(Construct):
    @property
    def function(self):
        return self._func
    @property
    def task(self):
        return self._task

    def __init__(self, scope: Construct, id: str, log_level: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        self._func = aws_lambda.Function(self,
            "PrepareRevisionMapInputFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset("../source/PrepareRevisionMapInputFunction"),
            handler="app.lambda_handler",
            environment={
                'LOG_LEVEL' : log_level,
                'Version' : Fn.find_in_map("SolutionInformation","SolutionDetails","Version")
            }
        )
        self._task = aws_stepfunctions_tasks.LambdaInvoke(self, 
            "PrepareRevisionMapInputTask",
            lambda_function=self._func
        )