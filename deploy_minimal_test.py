#!/usr/bin/env python3
"""
Deploy minimal test to diagnose Lambda issue
"""
import boto3
import zipfile
import tempfile
import os

AWS_REGION = 'us-east-1'
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

print("Deploying minimal test to logguardian-task-analyzer...")

# Create zip
zip_path = os.path.join(tempfile.gettempdir(), 'test.zip')
with zipfile.ZipFile(zip_path, 'w') as zipf:
    zipf.write('lambda_functions/test_minimal.py', 'lambda_function.py')

with open(zip_path, 'rb') as f:
    zip_content = f.read()

# Update
response = lambda_client.update_function_code(
    FunctionName='logguardian-task-analyzer',
    ZipFile=zip_content
)

print(f"Updated! Version: {response['Version']}")
print("Waiting for update...")

waiter = lambda_client.get_waiter('function_updated')
waiter.wait(FunctionName='logguardian-task-analyzer')

print("Ready! Test the URL now.")

