from constructs import Construct
from aws_cdk import (
    aws_stepfunctions,
    aws_stepfunctions_tasks,
    Duration
)

class CreateAndStartJob(Construct):
    @property
    def statemachine(self):
        return self._statemachine
    @property
    def task(self):
        return self._task
    def __init__(self, scope: Construct, id: str, check_job_status: aws_stepfunctions_tasks.LambdaInvoke, create_import_job: aws_stepfunctions_tasks.LambdaInvoke, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        choice_based_on_status = aws_stepfunctions.Choice(self,
            "ChoiceBaseOnStatus",
        )
        wait_processing = aws_stepfunctions.Wait(self,
            "WaitProcessing",
            time=aws_stepfunctions.WaitTime.duration(Duration.seconds(10))
        )
        jobpass = aws_stepfunctions.Pass(self, "JobSucceded")
        jobfail = aws_stepfunctions.Pass(self, "JobFailed")
        choice_based_on_status.when(
            condition=aws_stepfunctions.Condition.string_equals("$.Payload.JobStatus", "COMPLETED"),
            next=jobpass
        ),
        choice_based_on_status.when(
            condition=aws_stepfunctions.Condition.string_equals("$.Payload.JobStatus","IN_PROGRESS"),
            next=wait_processing
        )
        choice_based_on_status.when(
            condition=aws_stepfunctions.Condition.string_equals("$.Payload.JobStatus","ERROR"),
            next=jobfail
        )
        wait_processing.next(check_job_status)
        check_job_status.next(choice_based_on_status)

        # Create And Start Job StateMachine
        self._statemachine = aws_stepfunctions.StateMachine(self,
            "CreateAndStartJobStateMachine",
            definition=create_import_job.next(wait_processing)
        )

        #CreateAndStartJob Execution
        self._task = aws_stepfunctions_tasks.StepFunctionsStartExecution(self,
            "CreateAndStartImportJobSFN",
            state_machine=self._statemachine,
            input=aws_stepfunctions.TaskInput.from_object({
                "Comment":"Single ADX import job",
                "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                "JobMapIndex.$": "$.JobMapIndex",
                "Bucket.$": "$.Bucket",
                "Key.$": "$.Key",
                "DatasetId.$": "$.DatasetId",
                "RevisionId.$": "$.RevisionId",
                "RevisionMapIndex.$": "$.RevisionMapIndex"
            })            
        )