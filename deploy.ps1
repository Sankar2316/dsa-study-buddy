# DSA Study Buddy - ONE-CLICK DEPLOY (Windows PowerShell)
# Needs: Python 3.12, AWS CLI configured (aws configure, region us-east-1), Bedrock Nova Lite access
$ErrorActionPreference = "Continue"
$R = "us-east-1"; $FN = "dsa-study-buddy"; $TBL = "dsa-study-progress"
$ACC = (aws sts get-caller-identity --query Account --output text)
$BUCKET = "dsa-study-buddy-$ACC"
Write-Host "== Account $ACC ==" -ForegroundColor Cyan

# 1. DynamoDB
aws dynamodb describe-table --table-name $TBL --region $R 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  aws dynamodb create-table --table-name $TBL --region $R --billing-mode PAY_PER_REQUEST `
    --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=topic,AttributeType=S `
    --key-schema AttributeName=user_id,KeyType=HASH AttributeName=topic,KeyType=RANGE | Out-Null
  Write-Host "DynamoDB created"
}

# 2. IAM role
$ROLE = "$FN-role"
'{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' | Out-File trust.json -Encoding ascii
aws iam get-role --role-name $ROLE 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  aws iam create-role --role-name $ROLE --assume-role-policy-document file://trust.json | Out-Null
  foreach ($p in "service-role/AWSLambdaBasicExecutionRole","AmazonBedrockFullAccess","AmazonDynamoDBFullAccess") {
    aws iam attach-role-policy --role-name $ROLE --policy-arn "arn:aws:iam::aws:policy/$p" }
  Write-Host "Role created, waiting 15s..."; Start-Sleep 15
}
$ROLE_ARN = "arn:aws:iam::${ACC}:role/$ROLE"

# 3. Package
if (Test-Path package) { Remove-Item package -Recurse -Force }
pip install -r requirements.txt -t package --platform manylinux2014_x86_64 --only-binary=:all: --python-version 3.12 -q
Copy-Item agent.py, lambda_function.py package\
if (Test-Path function.zip) { Remove-Item function.zip }
Compress-Archive -Path package\* -DestinationPath function.zip

# 4. S3 bucket (code + website)
aws s3api head-bucket --bucket $BUCKET 2>$null
if ($LASTEXITCODE -ne 0) { aws s3 mb "s3://$BUCKET" --region $R | Out-Null }
aws s3 cp function.zip "s3://$BUCKET/function.zip" | Out-Null

# 5. Lambda
aws lambda get-function --function-name $FN --region $R 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  aws lambda create-function --function-name $FN --runtime python3.12 --role $ROLE_ARN `
    --handler lambda_function.lambda_handler --code S3Bucket=$BUCKET,S3Key=function.zip `
    --timeout 60 --memory-size 1024 --region $R `
    --environment "Variables={TABLE_NAME=$TBL,MODEL_ID=us.amazon.nova-lite-v1:0}" | Out-Null
} else {
  aws lambda update-function-code --function-name $FN --s3-bucket $BUCKET --s3-key function.zip --region $R | Out-Null
}
aws lambda wait function-active-v2 --function-name $FN --region $R
Write-Host "Lambda ready"

# 6. API Gateway (HTTP API quick-create)
$API_ID = (aws apigatewayv2 get-apis --region $R --query "Items[?Name=='$FN-api'].ApiId" --output text)
if (-not $API_ID) {
  $API_ID = (aws apigatewayv2 create-api --name "$FN-api" --protocol-type HTTP --region $R `
    --target "arn:aws:lambda:${R}:${ACC}:function:$FN" `
    --cors-configuration "AllowOrigins=*,AllowMethods=POST,OPTIONS,AllowHeaders=*" --query ApiId --output text)
  aws lambda add-permission --function-name $FN --statement-id apigw --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:${R}:${ACC}:${API_ID}/*" --region $R | Out-Null
}
$API_URL = "https://$API_ID.execute-api.$R.amazonaws.com"
Write-Host "API: $API_URL"

# 7. Frontend
(Get-Content index.html -Raw).Replace("REPLACE_WITH_API_URL/chat", "$API_URL/chat") | Out-File site.html -Encoding utf8
aws s3api put-public-access-block --bucket $BUCKET --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
"{""Version"":""2012-10-17"",""Statement"":[{""Effect"":""Allow"",""Principal"":""*"",""Action"":""s3:GetObject"",""Resource"":""arn:aws:s3:::$BUCKET/index.html""}]}" | Out-File policy.json -Encoding ascii
aws s3api put-bucket-policy --bucket $BUCKET --policy file://policy.json
aws s3 website "s3://$BUCKET" --index-document index.html
aws s3 cp site.html "s3://$BUCKET/index.html" --content-type "text/html" | Out-Null

Write-Host "`n===== DONE =====" -ForegroundColor Green
Write-Host "Live site : http://$BUCKET.s3-website-$R.amazonaws.com"
Write-Host "API       : $API_URL/chat"
