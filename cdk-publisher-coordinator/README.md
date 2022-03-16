# CDK Publisher Coordinator

install cdk via npm

```
npm install -g aws-cdk
```

init virtualenv and setup up environment
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

deploy
```
cdk deploy \
--parameters LogLevel=INFO \
--parameters LogBucketName=log-bucket-name \
--parameters LogBucketPrefix=log-bucket-prefix \
```

Required Parameters:
LogLevel, Minimum logging level to write out to CloudWatch
LogBucketName, Existing bucket to store server access logs associated with the manifest bucket
LogBucketPrefix, Prefix string (including the trailing slash); location for server access logs associated with the manifest bucket.

Optional Parameters:
AssetsPerRevision, Default 10000

Contexts (optional):
stackName, deploy a second Publisher-Coordinator Stack from the same repo
anonymousDataUsage, toggle solution helper metrics on and off
assetBucket, direct publisher-coordinator stack to a pre-deployed asset bucket
manifestBucket, direct publisher-coordinator stack to a pre-deployed manifest bucket