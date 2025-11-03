#!/usr/bin/env python3
"""
Deploy Lambda functions that use SageMaker endpoints
"""
import os
import sys
import json
import zipfile
import boto3
import time

# Credentials should be set in environment variables before running

AWS_REGION = 'us-east-1'
lambda_client = boto3.client('lambda', region_name=AWS_REGION)
iam_client = boto3.client('iam', region_name=AWS_REGION)

LAMBDA_FUNCTIONS = [
    {
        'name': 'logguardian-task-analyzer',
        'file': 'task_analyzer_sagemaker.py',
        'handler': 'task_analyzer_sagemaker.lambda_handler',
        'description': 'Analyzes tasks using NVIDIA LLM on SageMaker'
    },
    {
        'name': 'logguardian-task-executor',
        'file': 'task_executor_sagemaker.py',
        'handler': 'task_executor_sagemaker.lambda_handler',
        'description': 'Executes tasks autonomously via SageMaker'
    },
    {
        'name': 'logguardian-retrieval-agent',
        'file': 'retrieval_agent_sagemaker.py',
        'handler': 'retrieval_agent_sagemaker.lambda_handler',
        'description': 'Retrieval agent using NVIDIA Embeddings on SageMaker'
    }
]

print("=" * 60)
print("LAMBDA DEPLOYMENT - SageMaker Integration")
print("=" * 60)

def get_lambda_role():
    """Get existing Lambda role ARN"""
    try:
        role = iam_client.get_role(RoleName='logguardian-lambda-role')
        
        # Ensure SageMaker permissions
        try:
            iam_client.attach_role_policy(
                RoleName='logguardian-lambda-role',
                PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
            )
            print("[OK] SageMaker permissions added to Lambda role")
        except:
            pass  # Already attached
        
        return role['Role']['Arn']
    except:
        print("[ERROR] Lambda role not found. Creating...")
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        role = iam_client.create_role(
            RoleName='logguardian-lambda-role',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
            'arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
        ]
        
        for policy_arn in policies:
            iam_client.attach_role_policy(RoleName='logguardian-lambda-role', PolicyArn=policy_arn)
        
        time.sleep(10)
        return role['Role']['Arn']

def create_deployment_package(function_file):
    """Create ZIP package"""
    zip_path = f"lambda_functions/{function_file.replace('.py', '.zip')}"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(f"lambda_functions/{function_file}", function_file)
    
    return zip_path

def deploy_lambda(func_config, role_arn):
    """Deploy or update Lambda function"""
    function_name = func_config['name']
    
    print(f"\n[DEPLOY] {function_name}...")
    
    zip_path = create_deployment_package(func_config['file'])
    
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        lambda_client.get_function(FunctionName=function_name)
        
        print(f"[UPDATE] Updating function...")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"[OK] {function_name} updated")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"[CREATE] Creating function...")
        lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler=func_config['handler'],
            Code={'ZipFile': zip_content},
            Description=func_config['description'],
            Timeout=300,
            MemorySize=512
        )
        
        print(f"[OK] {function_name} created")
    
    os.remove(zip_path)
    return function_name

def test_lambda(function_name, test_payload):
    """Test Lambda function"""
    print(f"[TEST] Testing {function_name}...")
    
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
    print("\n[1/3] Getting Lambda role...")
    role_arn = get_lambda_role()
    
    print("\n[2/3] Deploying Lambda functions...")
    deployed = []
    
    for func_config in LAMBDA_FUNCTIONS:
        try:
            function_name = deploy_lambda(func_config, role_arn)
            deployed.append(function_name)
        except Exception as e:
            print(f"[ERROR] Failed to deploy {func_config['name']}: {str(e)}")
    
    print("\n[3/3] Testing functions...")
    
    test_lambda(
        'logguardian-task-analyzer',
        {'user_request': 'Analyze server logs for memory issues'}
    )
    
    test_lambda(
        'logguardian-retrieval-agent',
        {'action': 'search', 'text': 'memory problem', 'top_k': 3}
    )
    
    print("\n" + "=" * 60)
    print("LAMBDA DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print(f"\nDeployed {len(deployed)} functions:")
    for func in deployed:
        print(f"  - {func}")
    
    print("\nNext: Create web interface")

if __name__ == "__main__":
    main()

