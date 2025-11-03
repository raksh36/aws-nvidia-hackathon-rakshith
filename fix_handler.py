#!/usr/bin/env python3
"""
Fix Lambda handler configuration
"""
import boto3

AWS_REGION = 'us-east-1'
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

FUNCTIONS = [
    'logguardian-task-analyzer',
    'logguardian-task-executor',
    'logguardian-retrieval-agent'
]

print("=" * 70)
print("FIXING LAMBDA HANDLERS")
print("=" * 70)
print()

for func_name in FUNCTIONS:
    print(f"[...] {func_name}: Updating handler to lambda_function.lambda_handler...")
    
    try:
        response = lambda_client.update_function_configuration(
            FunctionName=func_name,
            Handler='lambda_function.lambda_handler'
        )
        
        print(f"[OK] {func_name}: Handler updated!")
        print(f"     Handler: {response['Handler']}")
        print()
        
    except Exception as e:
        print(f"[ERROR] {func_name}: {str(e)}")
        print()

print("=" * 70)
print("Handler configuration fixed!")
print("=" * 70)
print()
print("Now redeploy the Lambda functions with update_lambdas_quick.py")

