from constructs import Construct
from aws_cdk import (
    aws_s3,
    aws_iam
)

class PublisherCoordinatorBucket(Construct):
    @property
    def bucket(self):
        return self._bucket

    def __init__(self, scope: Construct, id: str, log_bucket: str, log_bucket_prefix: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        self._bucket = aws_s3.Bucket(self, 
            id,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=aws_s3.BlockPublicAccess(
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True
            ),
            server_access_logs_bucket=aws_s3.Bucket.from_bucket_name(self, "LogBucket", log_bucket),
            server_access_logs_prefix=log_bucket_prefix,
        )
        self._bucket.add_to_resource_policy(
            aws_iam.PolicyStatement(
                sid="HttpsOnly",
                actions=["*"],
                effect=aws_iam.Effect.DENY,
                resources=[
                    f"{self._bucket.bucket_arn}/*",
                ],
                principals=[aws_iam.AnyPrincipal()],
                conditions={
                    "Bool" : {
                        "aws:SecureTransport": "False"
                    }
                }
            )
        )
        self._bucket.add_to_resource_policy(
            aws_iam.PolicyStatement(
                sid="HttpsOnly",
                actions=["*"],
                effect=aws_iam.Effect.DENY,
                resources=[
                    self._bucket.bucket_arn,
                ],
                principals=[aws_iam.AnyPrincipal()],
                conditions={
                    "Bool" : {
                        "aws:SecureTransport": "False"
                    }
                }
            )
        )