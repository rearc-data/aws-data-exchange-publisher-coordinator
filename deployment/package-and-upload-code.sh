#!/usr/bin/env bash
#
# This assumes all of the OS-level configuration has been completed and git repo has already been cloned
#
# This script should be run from the repo's deployment directory
# cd deployment
# ./package-and-upload-code.sh code-bucket solution-name version
#
# Parameters:
#  - code-bucket: Name for the S3 bucket location where the code will be uploaded for record
#  - solution-name: name of the solution for consistency
#  - version: version of the package; for example v1.0.0

# Exit on error. Append "|| true" if you expect an error.
set -o errexit
# Exit on error inside any functions or subshells.
set -o errtrace

echo "check to see if input has been provided"
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Please provide all of the following values:"
    echo   "- the base source bucket name
            - solution name
            - version where the lambda code will eventually reside"
    echo "For example:
    ./package-and-upload-code.sh code-bucket solution-name version
    "
    exit 1
fi

CFN_CODE_BUCKET="$1"
SOLUTION_NAME="$2"
VERSION="$3"
MANIFEST_BUCKET="$4"
ASSET_BUCKET="$5"
MANIFEST_BUCKET_LOGGING_BUCKET="$6"
MANIFEST_BUCKET_LOGGING_PREFIX="$7"

echo "get reference for all important folders"
template_dir="$PWD"
template_dist_dir="$template_dir/global-s3-assets"
build_dist_dir="$template_dir/regional-s3-assets"
source_dir="$template_dir/../source"
layer_dir="$template_dir/../layer"

echo "------------------------------------------------------------------------------"
echo "[Init] Clean old dist, node_modules and bower_components folders"
echo "------------------------------------------------------------------------------"
echo "rm -rf $template_dist_dir"
rm -rf "$template_dist_dir"
echo "mkdir -p $template_dist_dir"
mkdir -p "$template_dist_dir"
echo "rm -rf $build_dist_dir"
rm -rf "$build_dist_dir"
echo "mkdir -p $build_dist_dir"
mkdir -p "$build_dist_dir"

echo "------------------------------------------------------------------------------"
echo "[Packing] Templates"
echo "------------------------------------------------------------------------------"
cp "$source_dir"/template.yaml "$template_dist_dir/"
cd "$template_dist_dir"
echo "Rename all *.yaml to *.template"
for f in *.yaml; do 
    mv -- "$f" "${f%.yaml}.template" | true
    cp "${f%.yaml}.template" "$source_dir/"
done

cd ..
echo "------------------------------------------------------------------------------"
echo "Updating custom values in CloudFormation template"
echo "------------------------------------------------------------------------------"

replace="s/%%BUCKET_NAME%%/$CFN_CODE_BUCKET/g"
echo "sed -i '' -e $replace $template_dist_dir/*.template"
sed -i '' -e "$replace" "$template_dist_dir"/*.template

replace="s/%%SOLUTION_NAME%%/$SOLUTION_NAME/g"
echo "sed -i '' -e $replace $template_dist_dir/*.template"
sed -i '' -e "$replace" "$template_dist_dir"/*.template

replace="s/%%VERSION%%/$VERSION/g"
echo "sed -i '' -e $replace $template_dist_dir/*.template"
sed -i '' -e "$replace" "$template_dist_dir"/*.template


echo "------------------------------------------------------------------------------"
echo "package source code"
echo "------------------------------------------------------------------------------"
zip -j $build_dist_dir/StartPublishingWorkflowFunction.zip $source_dir/StartPublishingWorkflowFunction/*
zip -j $build_dist_dir/PrepareRevisionMapInputFunction.zip $source_dir/PrepareRevisionMapInputFunction/*
zip -j $build_dist_dir/CreateRevisionAndPrepareJobMapInputFunction.zip $source_dir/CreateRevisionAndPrepareJobMapInputFunction/*
zip -j $build_dist_dir/CreateAndStartImportJobFunction.zip $source_dir/CreateAndStartImportJobFunction/*
zip -j $build_dist_dir/CheckJobStatusFunction.zip $source_dir/CheckJobStatusFunction/*
zip -j $build_dist_dir/FinalizeAndUpdateCatalogFunction.zip $source_dir/FinalizeAndUpdateCatalogFunction/*

echo "------------------------------------------------------------------------------"
echo "package lambda layer"
echo "------------------------------------------------------------------------------"
cd $layer_dir; zip -r $build_dist_dir/python_layer.zip python


echo "------------------------------------------------------------------------------"
echo "Upload code to the $CFN_CODE_BUCKET S3 bucket"
echo "------------------------------------------------------------------------------"
aws s3 cp $template_dist_dir "s3://$CFN_CODE_BUCKET/$SOLUTION_NAME/$VERSION/" --recursive --acl bucket-owner-full-control
aws s3 cp $build_dist_dir "s3://$CFN_CODE_BUCKET/$SOLUTION_NAME/$VERSION/" --recursive --acl bucket-owner-full-control
