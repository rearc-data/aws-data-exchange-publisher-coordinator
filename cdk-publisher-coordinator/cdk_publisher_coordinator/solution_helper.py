from constructs import Construct
from aws_cdk import (
    aws_lambda,
    CfnCustomResource,
    Fn
)

class SolutionHelper(Construct):
    @property
    def solution_uuid(self):
        return Fn.get_att(self._solution_uuid.logical_id,"UUID").to_string()

    def __init__(self, scope: Construct, id: str, log_level: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        solution_helper_func = aws_lambda.Function(self,
            "SolutionHelper",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset("../source/SolutionHelper"),
            handler="app.lambda_handler",
            environment={
                'LOG_LEVEL' : log_level,
                'AnonymousUsage' : Fn.find_in_map("Send","AnonymousUsage","Data")
            },
        )
        self._solution_uuid = CfnCustomResource(self, "SolutionUUID", service_token=solution_helper_func.function_arn)
        self._solution_uuid.add_property_override("CustomAction","CreateUuid")
        solution_lc = CfnCustomResource(self,"SolutionLifecycle",service_token=solution_helper_func.function_arn)
        solution_lc.add_property_override("CustomAction","LifecycleMetric")
        solution_lc.add_property_override("SolutionID", Fn.find_in_map("SolutionInformation", "SolutionDetails","Identifier"))
        solution_lc.add_property_override("UUID", Fn.get_att(self._solution_uuid.logical_id, "UUID"))
        solution_lc.add_property_override("Version",Fn.find_in_map("SolutionInformation","SolutionDetails","Version"))