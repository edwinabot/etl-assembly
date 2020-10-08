sam deploy \
    --s3-bucket sourcebucket-trustar-etl-assembly \
    --s3-prefix production \
    --region us-east-1 \
    --parameter-overrides \
        'EnvironmentName="production"' \
    --stack-name ETL-Assembly-Production \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile $1
