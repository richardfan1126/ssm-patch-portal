# SSM Patch Portal



## Demo

![](https://github.com/richardfan1126/ssm-patch-portal/raw/master/docs/demo.gif)

## Deployment guide

### Prerequisite

#### Local build
* [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_install)
* [npm](https://nodejs.org/en/download/)
* [npx](https://www.npmjs.com/package/npx)
* [Python3 and pip3](https://www.python.org/downloads/)
* [jq](https://stedolan.github.io/jq/download/) (Optional)

#### Docker build
* [Docker](https://docs.docker.com/get-docker/)

### Steps

1. Clone the repository

   ```bash
   git clone https://github.com/richardfan1126/ssm-patch-portal.git --recurse-submodules
   ```

1. Create a `.env` file inside project root

   Put in all the IAM Role ARNs that is attached to the targeted EC2 instances. This is for granting access to those EC2 instances over the S3 bucket containing install patch lists and command output.

   ```
   export PARAMETERS=Ec2IamRoleArns=<role_arn_1>,<role_arn_2>,...<role_arn_n>
   ```

1. Install and bootstrap required tools

   For AWS CDK, make sure you have already run the [bootstrap](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html#getting_started_bootstrap) command

   ```bash
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```

1. Run the deploy script

   (For local build)
   ```bash
   ./deploy.sh
   ```

   ---

   (For Docker build)

   Run `./docker-build/deploy.sh`.
   
   ```bash
   ./docker-build/deploy.sh
   ```
   
   When prompted, specify the location of aws credential.
   
   More detail on: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html#cli-configure-files-where. (Default: ~/.aws)
   
   ```bash
   Please specify the location of AWS credential [~/.aws] 
   ```

1. When prompted, go to the Amazon Cognito console (via the URL provided) and create an admin account.

   ```
   You can now create user in UserPool https://console.aws.amazon.com/cognito/users#/pool/xxxxxxxx/users
   ```

   Then press Y + \<Enter\> to continue the frontend deployment.

   ```
   Continue to deploy frontend stack? (Y/n) Y
   ```

1. When the deployment completes, you can go to the web portal via the URL provided.

   ```
   Outputs:
    SsmPatchPortalFrontend.PortalURL = https://xxxxxxxxxxxxxx.cloudfront.net
    Stack ARN:
    arn:aws:cloudformation:us-east-1:123456789012:stack/SsmPatchPortalFrontend/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   ```

## Architecture

![](https://raw.githubusercontent.com/richardfan1126/ssm-patch-portal/master/docs/architecture.jpg)

To be done
