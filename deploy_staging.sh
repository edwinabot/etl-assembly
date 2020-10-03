sam deploy \
    --s3-bucket sourcebucket-trustar-etl-assembly \
    --s3-prefix staging \
    --parameter-overrides \
        'ParameterKey=EnvironmentName,ParameterValue=Staging ParameterKey=SecurityGroupIds,ParameterValue="[sg-05b6b0659f231d6ce]" ParameterKey=SubnetIds,ParameterValue="[subnet-0307e55c069b91394, subnet-052358644cb97d659]"' \
    --stack-name ETL-Assembly-Staging \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile eco_admin
