from constructs import Construct
from aws_cdk import (
    aws_lambda,
    aws_iam,
    aws_stepfunctions,
    aws_stepfunctions_tasks
)

class FinalizeAndUpdateCatalog(Construct):
    @property
    def function(self):
        return self._func
    @property
    def task(self):
        return self._task

    def __init__(self, scope: Construct, id: str, log_level: str, role: aws_iam.IManagedPolicy, **kwargs):
        super().__init__(scope, id, **kwargs)

        finalize_and_update_catalog_role = aws_iam.Role(self,
            "FinalizeAndUpdateCatalogRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[role]
        )
        finalize_and_update_catalog_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "dataexchange:UpdateRevision",
                    "dataexchange:PublishDataSet",
                    "dataexchange:ListRevisionAssets",
                    "aws-marketplace:StartChangeSet",
                    "aws-marketplace:DescribeEntity",
                    "aws-marketplace:DescribeChangeSet"
                ],
                resources=["*"]
            )
        )
        self._func = aws_lambda.Function(self,
            "FinalizeAndUpdateCatalog",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset("../source/FinalizeAndUpdateCatalogFunction"),
            handler="app.lambda_handler",
            environment={
                'LOG_LEVEL' : log_level
            },
            role=finalize_and_update_catalog_role
        )
        self._task = aws_stepfunctions_tasks.LambdaInvoke(self,
            "FinalizeAndUpdateCatalogTask",
            lambda_function=self._func,
            input_path=aws_stepfunctions.JsonPath.string_at("$.Payload"),
        )