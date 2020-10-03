sam deploy \
    --s3-bucket sourcebucket-trustar-etl-assembly \
    --s3-prefix staging \
    --region us-east-1 \
    --parameter-overrides \
        'EnvironmentName="Staging" SecurityGroupId="sg-05b6b0659f231d6ce" SubnetIdAz0="subnet-0307e55c069b91394" SubnetIdAz1="subnet-052358644cb97d659"' \
    --stack-name ETL-Assembly-Staging \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile $1
