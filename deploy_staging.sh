sam deploy --s3-prefix staging --parameter-overrides 'ParameterKey=EnvironmentName,ParameterValue=Staging' --stack-name ETL-Assembly-Staging --tags 'application=etl-assembly,stage=Staging' --profile eco_ic