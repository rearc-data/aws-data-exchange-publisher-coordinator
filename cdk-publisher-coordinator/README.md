# CDK Publisher Coordinator

- [CDK Publisher Coordinator](#cdk-publisher-coordinator)
  - [Install cdk via npm](#install-cdk-via-npm)
  - [Deploy](#deploy)
  - [Required Parameters](#required-parameters)
  - [Optional Parameters](#optional-parameters)
  - [Contexts (optional)](#contexts-optional)

## Install cdk via npm

```
npm install -g aws-cdk
```

Init virtualenv and setup up environment
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Deploy
```
cdk deploy \
--parameters LogLevel=INFO \
--parameters LogBucketName=log-bucket-name \
--parameters LogBucketPrefix=log-bucket-prefix \
```

## Required Parameters
| name | description|
|-------|------------|
|LogLevel| Minimum logging level to write out to CloudWatch|
|LogBucketName| Existing bucket to store server access logs associated with the manifest bucket|
|LogBucketPrefix| Prefix string (including the trailing slash); location for server access logs associated with the manifest bucket|

## Optional Parameters
| name | description|
|-------|------------|
|AssetsPerRevision| Max number of assets in a revision |

## Contexts (optional)
| name | description|
|-------|------------|
|stackName| deploy a second Publisher-Coordinator Stack from the same repo|
|anonymousDataUsage| toggle solution helper metrics on and off|
|assetBucket| direct publisher-coordinator stack to a pre-deployed asset bucket|
|manifestBucket| direct publisher-coordinator stack to a pre-deployed manifest bucket