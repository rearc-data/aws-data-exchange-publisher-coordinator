<a href="https://www.rearc.io/data/">
    <img src="./rearc_logo_rgb.png" alt="Rearc Logo" title="Rearc Logo" height="52" />
</a>

## AWS Data Exchange Publisher Coordinator

This project sets up AWS Step Functions Workflow to automatically execute the publication steps for new dataset revisions for AWS Data Exchange (ADX) Products. Execution is triggered when a manifest file for a new revision is uploaded to the Manifest S3 bucket.

This project offers several improvements over [aws-data-exchange-publisher-coordinator](https://github.com/awslabs/aws-data-exchange-publisher-coordinator), addressing various [service limits](https://docs.aws.amazon.com/data-exchange/latest/userguide/limits.html) with AWS Data Exchange and improved logging. 

The following service limits have been addressed in this solution:
  - 10,000 assets per revision
  - 100 assets per import job and a maximum of 10 concurrent import jobs

### Usage
Below is the architecture diagram of this project:
<br/><br/>
<img src="./ADX-Publisher-Coordinator-Architecture.png" alt="ADX Publisher Coordinator Architecture" title="Amazon Data Exchange Publisher Coordinator Architecture" height="600" />
<br/><br/>
You should have the following prerequisites in place before running the code:
1. An AWS Data Exchange product and dataset
2. Three existing S3 buckets: 
    * AssetBucket: For uploading the assets
    * ManifestBucketLoggingBucket: For logging activities. Please find more information on here on how to [Create a Logging Amazon S3 bucket](https://docs.aws.amazon.com/solutions/latest/aws-data-exchange-publisher-coordinator/automated-deployment.html#create-a-logging-amazon-s3-bucket)
    * DistributionBucket: For uploading the Lambda code
3. Python 3.8+
4. AWS CLI
5. AWS SAM CLI

Once you have all prerequisites in place, clone the repository and update the code:

1. Update the `run.sh` file with desired values for the following variables including the names of the three pre-existing buckets you created above and a name for `ManifestBucket` which will be created by Cloudformation. 
```
SOLUTION_NAME='aws-data-exchange-publihser-coordinator' # name of the solution
SOLUTION_VERSION='1.0.0' # version number for the code
SOURCE_CODE_BUCKET=my-bucket-name # bucket where customized code will reside
MANIFEST_BUCKET='adx-publisher-coordinator-manifest-bucket-1234' # new bucket that will be created in this solution
ASSET_BUCKET='adx-publisher-coordinator-assets-bucket-1234' # Existing bucket where new assets are added.
MANIFEST_BUCKET_LOGGING_BUCKET='adx-publisher-coordinator-manifest-logging-bucket-1234' # Existing bucket where activity logs will be saved.
MANIFEST_BUCKET_LOGGING_PREFIX='adx-publisher-coordinator-logs/' # Prefix string for manifest bucket access logs (including the trailing slash).
LOGGING_LEVEL='INFO' # Logging level of the solution; accepted values: [ DEBUG, INFO, WARNING, ERROR, CRITICAL ]

STACK_NAME=my-stack-name # name of the cloudformation stack
REGION=us-east-1 # region where the cloudformation stack will be created
```

`run.sh` creates a `local` directory, replaces the names you specified in the Cloudformation template, packages the Lambda codes as zip files, uploads the code to the `$CFN_CODE_BUCKET` S3 bucket in your account using the AWS CLI, and finally builds and deploys the Cloudformation template using the AWS SAM CLI.

2. From the root directory of the project, run `run.sh`:
```
chmod +x run.sh
./run.sh
```

### Manifest File
Any time a manifest file is uploaded to the `ManifestBucket`, a Step Function execution pipeline is trigerred. The manifest file should follow a specific format:
- The of the manifest file should end with `.json`
- The size of the manifest file should be less than `10GB`
- The file should include a `JSON` object with the following format:
```
{
  "product_id": <PRODUCT_ID>,
  "dataset_id": <DATASET_ID>,
  "asset_list": [
    { "Bucket": <S3_BUCKET_NAME>, "Key": <S3_OBJECT_KEY> },
    { "Bucket": <S3_BUCKET_NAME>, "Key": <S3_OBJECT_KEY> },
    ...
  ]
}
```


### Contact Details
- If you find any issues with or have enhancement ideas for this product, open up a GitHub [issue](https://github.com/rearc-data/aws-data-exchange-publisher-coordinator/issues) and we will gladly take a look at it. Better yet, submit a pull request. Any contributions you make are greatly appreciated :heart:.
- If you have any questions or feedback, send us an email at data@rearc.io.

### About Rearc
Rearc is a cloud, software and services company. We believe that empowering engineers drives innovation. Cloud-native architectures, modern software and data practices, and the ability to safely experiment can enable engineers to realize their full potential. We have partnered with several enterprises and startups to help them achieve agility. Our approach is simple — empower engineers with the best tools possible to make an impact within their industry.
