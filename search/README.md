### Sample Usage

curl -i -X POST htcute-api.us-east-1.amazonaws.com/test/search --data "\"q=test\""

### Deployment

node_modules/serverless/bin/serverless deploy --aws-profile=default --stage=test
