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

   Input the value for the following parameters
   
   1. **Ec2IamRoleArns**
   
      All the IAM Role ARNs that is attached to the targeted EC2 instances. This is for granting access to those EC2 instances over the S3 bucket containing install patch lists and command output.

      ```
      export Ec2IamRoleArns=<role_arn_1>,<role_arn_2>,...,<role_arn_n>
      ```
   
   1. **AdminEmail**
      
      The email address where the initial admin password will be sent to. Make sure this email address can receive incoming mail.

      ```
      export AdminEmail=<admin_email_address>
      ```

1. (Optional) Install and bootstrap required tools

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

1. After the backend deployment, press Y + \<Enter\> to continue the frontend deployment.

   ```
   Continue to deploy frontend stack? (Y/n) Y
   ```

1. When the deployment completes, you can go to the web portal via the URL provided.

   Use the password, which was sent to your email, to login.

   ```
   Outputs:
    SsmPatchPortalFrontend.PortalURL = https://xxxxxxxxxxxxxx.cloudfront.net
    ...
   ```

## Cleanup

1. Delete CloudFormation Stacks

   1. **SsmPatchPortal**
   1. **SsmPatchPortalFrontend**

1. Empty and delete S3 buckets. (The bucket name have the following prefix)

   1. **ssmpatchportalfrontend-**
   1. **ssmpatchportal-s3bucketsta-**

1. Delete SSM associations

   1. **ssm-patch-portal-***<instance_id>*
   1. **ssm-patch-portal-scan**

## Architecture

![](https://raw.githubusercontent.com/richardfan1126/ssm-patch-portal/master/docs/architecture.jpg)