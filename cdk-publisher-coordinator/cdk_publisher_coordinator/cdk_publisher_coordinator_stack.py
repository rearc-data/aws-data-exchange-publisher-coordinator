from aws_cdk import (
    CfnMapping,
    CfnParameter,
    Stack,
    aws_s3,
    aws_s3_notifications,
    aws_iam
)
from constructs import Construct
from cdk_publisher_coordinator.create_and_start_job import CreateAndStartJob
from cdk_publisher_coordinator.finalize_and_update_catalog import FinalizeAndUpdateCatalog
from cdk_publisher_coordinator.publishing_revisions import PublishingRevisions
from cdk_publisher_coordinator.start_publishing_workflow import StartPublishingWorkflow
from cdk_publisher_coordinator.check_job_status import CheckJobStatus
from cdk_publisher_coordinator.create_and_start_import_job import CreateAndStartImportJob
from cdk_publisher_coordinator.create_revision_and_prepare_job_map_input import CreateRevisionAndPrepareJobMapInput
from cdk_publisher_coordinator.publsiher_coordinator_bucket import PublisherCoordinatorBucket
from cdk_publisher_coordinator.solution_helper import SolutionHelper
from cdk_publisher_coordinator.prepare_revision_input_map import PrepareRevisionInputMap

class CdkPublisherCoordinatorStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Parameter Definitions
        log_bucket_name = CfnParameter(self, "LogBucketName")
        log_bucket_prefix = CfnParameter(self, "LogBucketPrefix")
        log_level = CfnParameter(self,"LogLevel",allowed_values=["DEBUG","INFO","WARNING","ERROR","CRITICAL"])
        assets_per_revision = CfnParameter(self, "AssetsPerRevision", default="10000")
        #anonymous_data_usage = CfnParameter("self","AnonymousDataUsage",default="Yes")
        
        # Mappings
        CfnMapping(self,
            "Send",
            mapping={
                "AnonymousUsage":{
                    "Data": "Yes"
                }
            }
        )
        CfnMapping(self,
            "SolutionInformation", 
            mapping={
                "SolutionDetails":{
                    "Version" : "1.0.0",
                    "Identifier" : "SO0114"
                }
            }
        )

        # Managed Roles and Policies
        data_exchange_policy = aws_iam.ManagedPolicy.from_aws_managed_policy_name('AWSDataExchangeProviderFullAccess')
        aws_lambda_basic_exec_policy = aws_iam.ManagedPolicy.from_managed_policy_arn(self, 
            "LambdaExec", 
            managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )

        # Bucket Resources
        asset_bucket = PublisherCoordinatorBucket(self, "AssetBucket", 
            log_bucket= log_bucket_name.value_as_string,
            log_bucket_prefix=log_bucket_prefix.value_as_string
        )
        manifest_bucket = PublisherCoordinatorBucket(self, "ManifestBucket",
            log_bucket=log_bucket_name.value_as_string,
            log_bucket_prefix=log_bucket_prefix.value_as_string
        )

        # Solution Helper
        solution_hepler = SolutionHelper(self, "SolutionHelper",
            log_level=log_level.value_as_string
        )
        
        # Prepare Revision Map Input Function
        prepare_revision_map_input = PrepareRevisionInputMap(self,
            "PrepareRevisionMapInput",
            log_level=log_level.value_as_string
        )
        manifest_bucket.bucket.grant_read(prepare_revision_map_input.function)
        asset_bucket.bucket.grant_read(prepare_revision_map_input.function)
        prepare_revision_map_input.function.role.add_managed_policy(data_exchange_policy)

        # Create Revision and Prepare Job Map Input
        create_revision_and_prepare_job_map_input = CreateRevisionAndPrepareJobMapInput(self,
            "CreateRevisionAndPrepareJobMapInput",
            log_level=log_level.value_as_string,
            solution_uuid=solution_hepler.solution_uuid
        )
        manifest_bucket.bucket.grant_read(create_revision_and_prepare_job_map_input.function)
        asset_bucket.bucket.grant_read(create_revision_and_prepare_job_map_input.function)
        create_revision_and_prepare_job_map_input.function.role.add_managed_policy(data_exchange_policy)

        # Create And Start Import Job
        create_and_start_import_job = CreateAndStartImportJob(self,
            "CreateAndStartImportJob",
            log_level=log_level.value_as_string,
            solution_uuid=solution_hepler.solution_uuid
        )
        manifest_bucket.bucket.grant_read(create_and_start_import_job.function)
        asset_bucket.bucket.grant_read(create_and_start_import_job.function)
        create_and_start_import_job.function.role.add_managed_policy(data_exchange_policy)

        # CheckJobStatus
        check_job_status = CheckJobStatus(self,
            "CheckJobStatus",
            log_level=log_level.value_as_string,
            role=aws_lambda_basic_exec_policy
        )

        #FinalizeAndUpdateCatalog
        finalize_and_update_catalog = FinalizeAndUpdateCatalog(self,
            "FinalizeAndUpdateCatalog",
            log_level=log_level.value_as_string,
            role=aws_lambda_basic_exec_policy
        )

        # Create And Start Job StateMachine
        create_and_start_job = CreateAndStartJob(self,
            "CreateAndStartJob",
            check_job_status=check_job_status.task,
            create_import_job=create_and_start_import_job.task
        )
        
        #PublishingRevisionsStepFunction
        publishing_revisions = PublishingRevisions(self,
            "PublishingRevisions",
            create_and_start_job=create_and_start_job.statemachine,
            create_revision_and_prepare_job_map_input=create_revision_and_prepare_job_map_input.task,
            finalize_and_update_catalog=finalize_and_update_catalog.task,
            prepare_revision_input_map=prepare_revision_map_input.task
        )

        # Starter Lambda
        start_publishing_workflow = StartPublishingWorkflow(self,
            "StartPublishingWorkflow",
            log_level=log_level.value_as_string,
            assets_per_revision=assets_per_revision.value_as_string,
            state_machine_arn=publishing_revisions.statemachine.state_machine_arn
        )
        manifest_bucket.bucket.add_event_notification(aws_s3.EventType.OBJECT_CREATED,
            aws_s3_notifications.LambdaDestination(start_publishing_workflow.function),
            {"suffix":".json"}
        )
        manifest_bucket.bucket.grant_read_write(start_publishing_workflow.function)
        asset_bucket.bucket.grant_read(start_publishing_workflow.function)
        publishing_revisions.statemachine.grant_start_execution(start_publishing_workflow.function)