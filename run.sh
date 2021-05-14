#!/usr/bin/env bash

# Exit on error. Append "|| true" if you expect an error.
set -o errexit
# Exit on error inside any functions or subshells.
set -o errtrace

SOLUTION_NAME='<SOLUTION_NAME>' # name of the stack
VERSION='v1.0.0' # version number for the source code
CFN_CODE_BUCKET='<CODE_BUCKET_NAME>' # bucket where source code will reside
STACK_NAME='<CLOUDFORMATION_STACK_NAME>' # name of the cloudformation stack
REGION='us-east-1' # region where the cloudformation stack will be created

echo "------------------------------------------------------------------------------"
echo "SOLUTION_NAME=$SOLUTION_NAME"
echo "VERSION=$VERSION"
echo "CFN_CODE_BUCKET=$CFN_CODE_BUCKET"
echo "STACK_NAME=$STACK_NAME"
echo "REGION=$REGION"
echo "------------------------------------------------------------------------------"

echo "mkdir -p local"
rm -rf "local"
echo "rm -rf local"
mkdir -p "local"

echo "------------------------------------------------------------------------------"
echo "package and upload the Lambda code"
echo "------------------------------------------------------------------------------"
cd deployment
chmod +x ./package-and-upload-code.sh
./package-and-upload-code.sh "$CFN_CODE_BUCKET" "$SOLUTION_NAME" "$VERSION"

echo "------------------------------------------------------------------------------"
echo "Use AWS SAM to build and deploy the Cloudformation template" 
echo "------------------------------------------------------------------------------"
cd ../source
sam build
sam package --s3-bucket "$CFN_CODE_BUCKET" \
    --region "$REGION" \
    --output-template-file "../local/$SOLUTION_NAME-SAM.template"
sam deploy --template-file "../local/$SOLUTION_NAME-SAM.template" \
    --region "$REGION" --stack-name "$STACK_NAME" --capabilities CAPABILITY_IAM
