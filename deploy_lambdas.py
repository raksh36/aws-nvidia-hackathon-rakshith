#!/usr/bin/env python3
"""
Deploy Lambda functions for AgentOps
"""
import os
import sys
import json
import zipfile
import boto3
import time
from pathlib import Path

# Credentials from environment variables

AWS_REGION = 'us-east-1'
AWS_ACCOUNT_ID = '206192968156'

lambda_client = boto3.client('lambda', region_name=AWS_REGION)
iam_client = boto3.client('iam', region_name=AWS_REGION)

# Lambda functions to deploy
LAMBDA_FUNCTIONS = [
    {
        'name': 'logguardian-task-analyzer',
        'file': 'task_analyzer.py',
        'handler': 'task_analyzer.lambda_handler',
        'description': 'Analyzes tasks using NVIDIA LLM'
    },
    {
        'name': 'logguardian-task-executor',
        'file': 'task_executor.py',
        'handler': 'task_executor.lambda_handler',
        'description': 'Executes tasks autonomously'
    },
    {
        'name': 'logguardian-retrieval-agent',
        'file': 'retrieval_agent.py',
        'handler': 'retrieval_agent.lambda_handler',
        'description': 'Retrieval agent using NVIDIA Embeddings'
    }
]

def create_lambda_role():
    """Create IAM role for Lambda functions"""
    role_name = 'logguardian-lambda-role'
    
    try:
        # Check if role exists
        role = iam_client.get_role(RoleName=role_name)
        print(f"[EXISTS] IAM role {role_name} already exists")
        return role['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        print(f"[CREATE] Creating IAM role {role_name}...")
        
        # Trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create role
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Execution role for AgentOps Lambda functions'
        )
        
        # Attach policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
        ]
        
        for policy_arn in policies:
            iam_client.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        
        print(f"[OK] IAM role created: {role['Role']['Arn']}")
        
        # Wait for role to propagate
        print("[WAIT] Waiting for IAM role to propagate...")
        time.sleep(10)
        
        return role['Role']['Arn']

def create_deployment_package(function_file):
    """Create deployment ZIP package for Lambda"""
    zip_path = f"lambda_functions/{function_file.replace('.py', '.zip')}"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the function file
        zipf.write(f"lambda_functions/{function_file}", function_file)
    
    return zip_path

def deploy_lambda_function(func_config, role_arn):
    """Deploy or update a Lambda function"""
    function_name = func_config['name']
    
    print(f"\n[DEPLOY] {function_name}...")
    
    # Create deployment package
    zip_path = create_deployment_package(func_config['file'])
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Check if function exists
        lambda_client.get_function(FunctionName=function_name)
        
        # Update existing function
        print(f"[UPDATE] Updating function code...")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"[OK] {function_name} updated successfully")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        print(f"[CREATE] Creating new function...")
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler=func_config['handler'],
            Code={'ZipFile': zip_content},
            Description=func_config['description'],
            Timeout=300,  # 5 minutes
            MemorySize=512,
            Environment={
                'Variables': {
                    'NVIDIA_API_KEY': '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'
                }
            }
        )
        
        print(f"[OK] {function_name} created successfully")
    
    # Clean up ZIP file
    os.remove(zip_path)
    
    return function_name

def test_lambda_function(function_name, test_payload):
    """Test a Lambda function"""
    print(f"\n[TEST] Testing {function_name}...")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print(f"[OK] Test passed")
            return True
        else:
            print(f"[FAIL] Test failed: {result}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test error: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("LAMBDA DEPLOYMENT - AgentOps")
    print("=" * 60)
    
    # Step 1: Create IAM role
    print("\n[1/3] Setting up IAM role...")
    role_arn = create_lambda_role()
    
    # Step 2: Deploy Lambda functions
    print("\n[2/3] Deploying Lambda functions...")
    deployed_functions = []
    
    for func_config in LAMBDA_FUNCTIONS:
        try:
            function_name = deploy_lambda_function(func_config, role_arn)
            deployed_functions.append(function_name)
        except Exception as e:
            print(f"[ERROR] Failed to deploy {func_config['name']}: {str(e)}")
    
    # Step 3: Test functions
    print("\n[3/3] Testing deployed functions...")
    
    # Test Task Analyzer
    test_lambda_function(
        'logguardian-task-analyzer',
        {'user_request': 'Analyze logs for errors'}
    )
    
    # Test Retrieval Agent
    test_lambda_function(
        'logguardian-retrieval-agent',
        {'action': 'search', 'text': 'memory issue', 'top_k': 3}
    )
    
    print("\n" + "=" * 60)
    print("DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print(f"\nDeployed {len(deployed_functions)} Lambda functions:")
    for func in deployed_functions:
        print(f"  - {func}")
    
    print("\nNext: Create API Gateway and web interface")

if __name__ == "__main__":
    main()

