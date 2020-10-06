sam deploy \
    --s3-bucket sourcebucket-trustar-etl-assembly \
    --s3-prefix staging \
    --region us-east-1 \
    --parameter-overrides \
        'EnvironmentName="Staging"' \
    --stack-name ETL-Assembly-Staging \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile $1
