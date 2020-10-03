sam deploy \
    --s3-bucket sourcebucket-trustar-etl-assembly \
    --s3-prefix production \
    --region us-east-1 \
    --parameter-overrides \
        'EnvironmentName="Production" SecurityGroupId="sg-0718d5cd3a6119947" SubnetIdAz0="subnet-0f2f8aad02e17bf4d" SubnetIdAz1="subnet-032c0f59550930451"' \
    --stack-name ETL-Assembly-Production \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile $1
