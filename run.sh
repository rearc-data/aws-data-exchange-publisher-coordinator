#!/usr/bin/env bash

# Exit on error. Append "|| true" if you expect an error.
set -o errexit
# Exit on error inside any functions or subshells.
set -o errtrace

export CFN_CODE_BUCKET='<CODE_Bucket_NAME>' # bucket where source code will reside
export SOLUTION_NAME='<CLOUDFORMATION_STACK_NAME>' # name of the stack
export VERSION='v1.0.0' # version number for the source code

echo "creating the 'local' directory"
mkdir -p 'local'

echo "package the Lambda codes for upload"
cd deployment
chmod +x ./package-codes-for-upload.sh
./package-codes-for-upload.sh "$CFN_CODE_BUCKET" "$SOLUTION_NAME" "$VERSION"

echo "Upload code to the $CFN_CODE_BUCKET S3 bucket"
aws s3 cp ./global-s3-assets "s3://$CFN_CODE_BUCKET/$SOLUTION_NAME/$VERSION/" --recursive --acl bucket-owner-full-control
aws s3 cp ./regional-s3-assets "s3://$CFN_CODE_BUCKET/$SOLUTION_NAME/$VERSION/" --recursive --acl bucket-owner-full-control

echo "Use AWS SAM to build and deploy the Cloudformation template" 
cd ../source
region='us-east-1'
stack_name='adx-publisher-workflow-test'
sam build
sam package --s3-bucket "$CFN_CODE_BUCKET" \
     --output-template-file "../local/$SOLUTION_NAME-SAM.template"
sam deploy --template-file "../local/$SOLUTION_NAME-SAM.template" \
    --region "$region" --stack-name "$stack_name" --capabilities CAPABILITY_IAM #CAPABILITY_NAMED_IAM #CAPABILITY_IAM
