from constructs import Construct
from aws_cdk import (
    aws_stepfunctions,
    aws_stepfunctions_tasks,
    Duration,
    aws_logs
)

class PublishingRevisions(Construct):
    @property
    def statemachine(self):
        return self._statemachine
    
    def __init__(self, scope: Construct, id: str, create_and_start_job: aws_stepfunctions.StateMachine, create_revision_and_prepare_job_map_input: aws_stepfunctions_tasks.LambdaInvoke, finalize_and_update_catalog: aws_stepfunctions_tasks.LambdaInvoke, prepare_revision_input_map: aws_stepfunctions_tasks.LambdaInvoke, **kwargs):
        super().__init__(scope, id, **kwargs)
        create_revision_map = aws_stepfunctions.Map(self, 
            "CreateRevisionsMap",
            input_path=aws_stepfunctions.JsonPath.string_at("$.Payload"),
            items_path=aws_stepfunctions.JsonPath.string_at("$.RevisionMapInput"),
            max_concurrency=1,
            result_path=aws_stepfunctions.JsonPath.string_at("$.RevisionDetails1.$"),
            parameters={
                    "RevisionMapIndex.$": "$$.Map.Item.Value",
                    "Bucket.$": "$.Bucket",
                    "Key.$": "$.Key",
                    "ProductId.$": "$.ProductId",
                    "DatasetId.$": "$.DatasetId"
            }
        )

        create_and_start_import_assets_map = aws_stepfunctions.Map(self,
            "CreateAndStartAnImportAssetsJobMap",
            input_path=aws_stepfunctions.JsonPath.string_at("$.Payload"),
            items_path=aws_stepfunctions.JsonPath.string_at("$.JobMapInput"),
            max_concurrency=10,
            parameters={
                "JobMapIndex.$": "$$.Map.Item.Value",
                "Bucket.$": "$.Bucket",
                "Key.$": "$.Key",
                "ProductId.$": "$.ProductId",
                "DatasetId.$": "$.DatasetId",
                "RevisionId.$": "$.RevisionId",
                "RevisionMapIndex.$": "$.RevisionMapIndex"    
            },
            result_path=aws_stepfunctions.JsonPath.string_at("$.RevisionDetails2.$")
        )

        create_and_start_job_sfn = aws_stepfunctions_tasks.StepFunctionsStartExecution(self,
            "CreateAndStartImportJobSFN",
            state_machine=create_and_start_job,
            input=aws_stepfunctions.TaskInput.from_object({
                "Comment":"Single ADX import job",
                "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                "JobMapIndex.$": "$.JobMapIndex",
                "Bucket.$": "$.Bucket",
                "Key.$": "$.Key",
                "ProductId.$": "$.ProductId",
                "DatasetId.$": "$.DatasetId",
                "RevisionId.$": "$.RevisionId",
                "RevisionMapIndex.$": "$.RevisionMapIndex"
            })            
        )
        sfn_wait = aws_stepfunctions.Wait(self,
            "WaitForSFN",
            time=aws_stepfunctions.WaitTime.duration(Duration.seconds(10))
        )
        create_revision_map.iterator(create_revision_and_prepare_job_map_input)
        create_revision_and_prepare_job_map_input.next(create_and_start_import_assets_map)
        create_and_start_import_assets_map.iterator(create_and_start_job_sfn)
        create_and_start_import_assets_map.next(sfn_wait)
        sfn_wait.next(finalize_and_update_catalog)
        self._statemachine= aws_stepfunctions.StateMachine(self, "PublishRevisionFunction",
            definition=prepare_revision_input_map.next(create_revision_map),
            timeout=Duration.seconds(10800),
            logs=aws_stepfunctions.LogOptions(
                destination=aws_logs.LogGroup(self, "CDKPDC"),
                level=aws_stepfunctions.LogLevel.ALL
            )
        )