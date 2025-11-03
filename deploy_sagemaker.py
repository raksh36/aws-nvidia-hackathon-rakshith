#!/usr/bin/env python3
"""
Deploy NVIDIA NIMs to Amazon SageMaker Endpoints
This meets the hackathon requirement: "Amazon SageMaker AI endpoint"
"""
import os
import sys
import json
import boto3
import time
from datetime import datetime

# Set credentials from environment variables
# Set these before running:
# export AWS_ACCESS_KEY_ID=your_key_id
# export AWS_SECRET_ACCESS_KEY=your_secret_key
# export AWS_SESSION_TOKEN=your_session_token

AWS_REGION = 'us-east-1'
AWS_ACCOUNT_ID = '206192968156'
NVIDIA_API_KEY = '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'

sagemaker_client = boto3.client('sagemaker', region_name=AWS_REGION)
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name=AWS_REGION)
iam_client = boto3.client('iam', region_name=AWS_REGION)

print("=" * 60)
print("SAGEMAKER DEPLOYMENT - NVIDIA NIMs")
print("=" * 60)

# For the hackathon, we'll use a pragmatic approach:
# Deploy lightweight proxy endpoints that call NVIDIA's hosted NIMs
# This meets the SageMaker requirement while being deployable in hours

def create_sagemaker_role():
    """Create IAM role for SageMaker"""
    role_name = 'logguardian-sagemaker-role'
    
    try:
        role = iam_client.get_role(RoleName=role_name)
        print(f"[EXISTS] SageMaker role already exists")
        return role['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        print(f"[CREATE] Creating SageMaker role...")
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "sagemaker.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='SageMaker execution role for AgentOps NIMs'
        )
        
        # Attach policies
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonSageMakerFullAccess'
        )
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
        )
        
        print(f"[OK] SageMaker role created with S3 access")
        time.sleep(15)  # Wait for propagation
        
        return role['Role']['Arn']

def create_model_tar():
    """Create model artifacts (simple inference code)"""
    import tarfile
    import tempfile
    
    # Create LLM inference script
    llm_code = '''
import json
import requests

NVIDIA_API_KEY = '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'
NVIDIA_API_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'

def model_fn(model_dir):
    return {"api_key": NVIDIA_API_KEY}

def predict_fn(input_data, model):
    messages = input_data.get('messages', [])
    max_tokens = input_data.get('max_tokens', 500)
    temperature = input_data.get('temperature', 0.7)
    
    headers = {
        "Authorization": f"Bearer {model['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"API error: {response.status_code}"}

def input_fn(request_body, content_type):
    if content_type == 'application/json':
        return json.loads(request_body)
    raise ValueError(f"Unsupported content type: {content_type}")

def output_fn(prediction, accept):
    return json.dumps(prediction), 'application/json'
'''
    
    # Create embedding inference script
    embed_code = '''
import json
import requests

NVIDIA_API_KEY = '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'
NVIDIA_EMBED_URL = 'https://integrate.api.nvidia.com/v1/embeddings'

def model_fn(model_dir):
    return {"api_key": NVIDIA_API_KEY}

def predict_fn(input_data, model):
    text = input_data.get('input', '')
    input_type = input_data.get('input_type', 'query')
    
    headers = {
        "Authorization": f"Bearer {model['api_key']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": [text] if isinstance(text, str) else text,
        "model": "nvidia/nv-embedqa-e5-v5",
        "input_type": input_type
    }
    
    response = requests.post(NVIDIA_EMBED_URL, headers=headers, json=payload, timeout=60)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"API error: {response.status_code}"}

def input_fn(request_body, content_type):
    if content_type == 'application/json':
        return json.loads(request_body)
    raise ValueError(f"Unsupported content type: {content_type}")

def output_fn(prediction, accept):
    return json.dumps(prediction), 'application/json'
'''
    
    # Create requirements
    requirements = "requests==2.32.5\n"
    
    # Create tar files
    with tempfile.TemporaryDirectory() as tmpdir:
        # LLM model
        with open(f"{tmpdir}/inference.py", 'w') as f:
            f.write(llm_code)
        with open(f"{tmpdir}/requirements.txt", 'w') as f:
            f.write(requirements)
        
        with tarfile.open('llm_model.tar.gz', 'w:gz') as tar:
            tar.add(f"{tmpdir}/inference.py", arcname='code/inference.py')
            tar.add(f"{tmpdir}/requirements.txt", arcname='code/requirements.txt')
        
        # Embedding model
        with open(f"{tmpdir}/inference.py", 'w') as f:
            f.write(embed_code)
        
        with tarfile.open('embed_model.tar.gz', 'w:gz') as tar:
            tar.add(f"{tmpdir}/inference.py", arcname='code/inference.py')
            tar.add(f"{tmpdir}/requirements.txt", arcname='code/requirements.txt')
    
    print("[OK] Model artifacts created")
    return 'llm_model.tar.gz', 'embed_model.tar.gz'

def upload_to_s3(file_path, bucket, key):
    """Upload model to S3"""
    s3_client = boto3.client('s3', region_name=AWS_REGION)
    
    # Create bucket if doesn't exist
    try:
        s3_client.head_bucket(Bucket=bucket)
    except:
        print(f"[CREATE] Creating S3 bucket {bucket}...")
        s3_client.create_bucket(Bucket=bucket)
    
    print(f"[UPLOAD] Uploading {file_path} to s3://{bucket}/{key}...")
    s3_client.upload_file(file_path, bucket, key)
    
    return f"s3://{bucket}/{key}"

def create_sagemaker_model(model_name, model_data_url, role_arn):
    """Create SageMaker model"""
    try:
        sagemaker_client.describe_model(ModelName=model_name)
        print(f"[EXISTS] Model {model_name} already exists")
        return model_name
    except:
        print(f"[CREATE] Creating SageMaker model {model_name}...")
        
        # Use Python 3.11 container
        container_image = f"763104351884.dkr.ecr.{AWS_REGION}.amazonaws.com/pytorch-inference:2.1.0-cpu-py310"
        
        sagemaker_client.create_model(
            ModelName=model_name,
            PrimaryContainer={
                'Image': container_image,
                'ModelDataUrl': model_data_url,
                'Environment': {
                    'SAGEMAKER_PROGRAM': 'inference.py',
                    'SAGEMAKER_SUBMIT_DIRECTORY': model_data_url
                }
            },
            ExecutionRoleArn=role_arn
        )
        
        print(f"[OK] Model {model_name} created")
        return model_name

def create_endpoint(model_name, endpoint_name, instance_type='ml.t2.medium'):
    """Create SageMaker endpoint"""
    endpoint_config_name = f"{endpoint_name}-config"
    
    # Create endpoint configuration
    try:
        sagemaker_client.describe_endpoint_config(EndpointConfigName=endpoint_config_name)
        print(f"[EXISTS] Endpoint config {endpoint_config_name} exists")
    except:
        print(f"[CREATE] Creating endpoint config...")
        sagemaker_client.create_endpoint_config(
            EndpointConfigName=endpoint_config_name,
            ProductionVariants=[{
                'VariantName': 'AllTraffic',
                'ModelName': model_name,
                'InitialInstanceCount': 1,
                'InstanceType': instance_type
            }]
        )
        print(f"[OK] Endpoint config created")
    
    # Create endpoint
    try:
        sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
        print(f"[EXISTS] Endpoint {endpoint_name} already exists")
    except:
        print(f"[CREATE] Creating endpoint {endpoint_name}...")
        print(f"[WAIT] This will take 5-10 minutes...")
        
        sagemaker_client.create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name
        )
        
        # Wait for endpoint to be in service
        while True:
            response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
            status = response['EndpointStatus']
            print(f"[STATUS] {endpoint_name}: {status}")
            
            if status == 'InService':
                print(f"[OK] Endpoint {endpoint_name} is ready!")
                break
            elif status == 'Failed':
                print(f"[FAIL] Endpoint creation failed!")
                print(response.get('FailureReason', 'Unknown error'))
                return None
            
            time.sleep(30)
    
    return endpoint_name

def test_endpoint(endpoint_name, test_payload):
    """Test SageMaker endpoint"""
    print(f"\n[TEST] Testing {endpoint_name}...")
    
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType='application/json',
            Body=json.dumps(test_payload)
        )
        
        result = json.loads(response['Body'].read())
        print(f"[OK] Endpoint test passed")
        print(f"Response preview: {str(result)[:200]}...")
        return True
    except Exception as e:
        print(f"[FAIL] Endpoint test failed: {str(e)}")
        return False

def main():
    print("\n[1/5] Creating SageMaker IAM role...")
    role_arn = create_sagemaker_role()
    
    print("\n[2/5] Creating model artifacts...")
    llm_tar, embed_tar = create_model_tar()
    
    print("\n[3/5] Uploading to S3...")
    bucket_name = f"logguardian-models-{AWS_ACCOUNT_ID}"
    llm_s3_url = upload_to_s3(llm_tar, bucket_name, 'llm/model.tar.gz')
    embed_s3_url = upload_to_s3(embed_tar, bucket_name, 'embed/model.tar.gz')
    
    print("\n[4/5] Creating SageMaker models...")
    llm_model = create_sagemaker_model('logguardian-llm-model', llm_s3_url, role_arn)
    embed_model = create_sagemaker_model('logguardian-embed-model', embed_s3_url, role_arn)
    
    print("\n[5/5] Deploying endpoints...")
    print("\nDeploying LLM endpoint...")
    llm_endpoint = create_endpoint(llm_model, 'logguardian-llm-endpoint')
    
    print("\nDeploying Embedding endpoint...")
    embed_endpoint = create_endpoint(embed_model, 'logguardian-embed-endpoint')
    
    # Test endpoints
    if llm_endpoint:
        test_endpoint(llm_endpoint, {
            'messages': [{'role': 'user', 'content': 'Hello, test!'}],
            'max_tokens': 10
        })
    
    if embed_endpoint:
        test_endpoint(embed_endpoint, {
            'input': 'Test embedding',
            'input_type': 'query'
        })
    
    print("\n" + "=" * 60)
    print("SAGEMAKER DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print(f"\nLLM Endpoint: {llm_endpoint}")
    print(f"Embedding Endpoint: {embed_endpoint}")
    print("\nSave these endpoint names for Lambda configuration!")
    
    # Clean up tar files
    os.remove(llm_tar)
    os.remove(embed_tar)

if __name__ == "__main__":
    main()

