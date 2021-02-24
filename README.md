# ETL Assembly

## MISP automated flow POC

This is the implementation of MISP automated flow. Here we also explore a new architecture for hooking sources and app on our ecosystem.

More docs to come...

## Environment setup

Assuming you already have [Pipenv](https://pipenv.pypa.io/en/latest/install/#installing-pipenv) and [pre-commit](https://pre-commit.com/) installed on your OS do:

```shell
pipenv install --dev
pre-commit install
```

This will create the virtual environment for this project and install dependencies including dev ones. Also pre commit hooks are going to be created and activated.

# etl-assembly (SAM App)

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. It includes the following files and folders.

- hello_world - Code for the application's Lambda function.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code.
- template.yaml - A template that defines the application's AWS resources.

The application uses several AWS resources, including Lambda functions and an API Gateway API. These resources are defined in the `template.yaml` file in this project. You can update the template to add AWS resources through the same deployment process that updates your application code.

If you prefer to use an integrated development environment (IDE) to build and test your application, you can use the AWS Toolkit.
The AWS Toolkit is an open source plug-in for popular IDEs that uses the SAM CLI to build and deploy serverless applications on AWS. The AWS Toolkit also adds a simplified step-through debugging experience for Lambda function code. See the following links to get started.

* [PyCharm](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [IntelliJ](https://docs.aws.amazon.com/toolkit-for-jetbrains/latest/userguide/welcome.html)
* [VS Code](https://docs.aws.amazon.com/toolkit-for-vscode/latest/userguide/welcome.html)
* [Visual Studio](https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/welcome.html)

# Building and deploying Staging and Production stacks

Before deploying you need to build the application by doing:

```bash
# Build the SAM app
sam build
```

At the root of this project you can find the `devops` directory. There are two bash scripts for deploying the stack:

```bash
# Staging deploy
bash devops/deploy_staging.sh an_aws_profile
```

```bash
# Prod deploy
bash devops/deploy_production.sh an_aws_profile
```
