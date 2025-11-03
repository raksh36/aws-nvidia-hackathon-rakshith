#!/usr/bin/env python3
"""
Update Lambda functions with dependencies (requests library)
"""
import boto3
import zipfile
import tempfile
import os
import subprocess
import sys

AWS_REGION = 'us-east-1'
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

print("=" * 70)
print("UPDATING TASK EXECUTOR WITH DEPENDENCIES")
print("=" * 70)
print()

# Install requests to a temp directory
print("[1/3] Installing dependencies...")
temp_dir = tempfile.mkdtemp()
subprocess.check_call([
    sys.executable, '-m', 'pip', 'install',
    'requests',
    '-t', temp_dir,
    '--quiet'
])
print("      [OK] Dependencies installed")
print()

# Create deployment package
print("[2/3] Creating deployment package...")
zip_path = os.path.join(tempfile.gettempdir(), 'task_executor_with_deps.zip')

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Add Lambda function code
    zipf.write('lambda_functions/task_executor_sagemaker.py', 'lambda_function.py')
    
    # Add dependencies
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, temp_dir)
            zipf.write(file_path, arcname)

print("      [OK] Package created")
print()

# Upload to Lambda
print("[3/3] Updating Lambda function...")
with open(zip_path, 'rb') as f:
    zip_content = f.read()

response = lambda_client.update_function_code(
    FunctionName='logguardian-task-executor',
    ZipFile=zip_content
)

print(f"      [OK] Function updated: {response['Version']}")
print()

# Wait for update
print("      Waiting for update to complete...")
waiter = lambda_client.get_waiter('function_updated')
waiter.wait(FunctionName='logguardian-task-executor')

print("      [OK] Update complete!")
print()

print("=" * 70)
print("TASK EXECUTOR NOW HAS RETRIEVAL INTEGRATION!")
print("=" * 70)
print()
print("Test it now - it will call the Retrieval Agent for context!")

