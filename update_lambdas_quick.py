#!/usr/bin/env python3
"""
Quick Lambda update - just push new code without recreating everything
"""
import boto3
import zipfile
import os
import time
import tempfile

AWS_REGION = 'us-east-1'
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

FUNCTIONS = {
    'logguardian-task-analyzer': 'task_analyzer_sagemaker.py',
    'logguardian-task-executor': 'task_executor_sagemaker.py',
    'logguardian-retrieval-agent': 'retrieval_agent_sagemaker.py'
}

def update_lambda_code(function_name, lambda_file):
    """Update Lambda function code"""
    print(f"[...] {function_name}: Creating deployment package...")
    
    # Create zip file
    zip_path = os.path.join(tempfile.gettempdir(), f'{function_name}.zip')
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        lambda_path = f'lambda_functions/{lambda_file}'
        zipf.write(lambda_path, 'lambda_function.py')
    
    # Read zip contents
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    print(f"[...] {function_name}: Uploading new code...")
    
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"[OK] {function_name}: Code updated!")
        print(f"     Version: {response['Version']}")
        
        # Wait for update to complete
        print(f"[...] {function_name}: Waiting for update to complete...")
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=function_name)
        
        print(f"[OK] {function_name}: Ready!")
        return True
        
    except Exception as e:
        print(f"[ERROR] {function_name}: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("UPDATING LAMBDA FUNCTIONS (CORS FIX)")
    print("=" * 70)
    print()
    
    success_count = 0
    
    for func_name, lambda_file in FUNCTIONS.items():
        if update_lambda_code(func_name, lambda_file):
            success_count += 1
        print()
    
    print("=" * 70)
    print(f"COMPLETE: {success_count}/{len(FUNCTIONS)} functions updated")
    print("=" * 70)
    print()
    print("Web interface should now work without CORS errors!")
    print("Test at: https://raksh36.github.io/aws-nvidia-hackathon-rakshith/")

if __name__ == '__main__':
    main()

