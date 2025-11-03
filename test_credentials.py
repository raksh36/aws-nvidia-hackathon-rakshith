#!/usr/bin/env python3
"""
Quick credential verification script
"""
import os
import json
import sys

# AWS credentials should be set in environment variables before running:
# export AWS_ACCESS_KEY_ID=your_key
# export AWS_SECRET_ACCESS_KEY=your_secret
# export AWS_SESSION_TOKEN=your_token
# export AWS_DEFAULT_REGION=us-east-1

NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY', 'your-nvidia-api-key-here')

print("=" * 60)
print("CREDENTIAL VERIFICATION")
print("=" * 60)

# Test 1: AWS Credentials
print("\n[1] Testing AWS Credentials...")
try:
    import boto3
    sts = boto3.client('sts', region_name='us-east-1')
    identity = sts.get_caller_identity()
    print(f"   [OK] AWS Access CONFIRMED!")
    print(f"   Account: {identity['Account']}")
    print(f"   User ARN: {identity['Arn']}")
    
    # Test DynamoDB access
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    tables = dynamodb.list_tables()
    print(f"   [OK] DynamoDB access works! ({len(tables.get('TableNames', []))} tables)")
    
    # Test Lambda access
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    functions = lambda_client.list_functions()
    print(f"   [OK] Lambda access works! ({len(functions.get('Functions', []))} functions)")
    
except Exception as e:
    print(f"   [FAIL] AWS Access FAILED: {str(e)}")
    sys.exit(1)

# Test 2: NVIDIA API
print("\n[2] Testing NVIDIA NIM API...")
try:
    import requests
    
    # Test the LLaMA NIM endpoint
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta/llama-3.1-8b-instruct",
        "messages": [{"role": "user", "content": "Say 'API works!' in 2 words"}],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        message = result['choices'][0]['message']['content']
        print(f"   [OK] NVIDIA NIM CONFIRMED!")
        print(f"   Response: {message}")
    else:
        print(f"   [FAIL] NVIDIA API returned: {response.status_code}")
        print(f"   Error: {response.text[:200]}")
        sys.exit(1)
        
except Exception as e:
    print(f"   [FAIL] NVIDIA API FAILED: {str(e)}")
    sys.exit(1)

# Test 3: Embedding API
print("\n[3] Testing NVIDIA Embedding API...")
try:
    embed_url = "https://integrate.api.nvidia.com/v1/embeddings"
    embed_payload = {
        "input": ["Test embedding"],
        "model": "nvidia/nv-embedqa-e5-v5",
        "input_type": "query"
    }
    
    response = requests.post(embed_url, headers=headers, json=embed_payload, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        embedding_dim = len(result['data'][0]['embedding'])
        print(f"   [OK] NVIDIA Embedding API CONFIRMED!")
        print(f"   Embedding dimension: {embedding_dim}")
    else:
        print(f"   [WARN] Embedding API returned: {response.status_code}")
        print(f"   (This is optional, continuing...)")
        
except Exception as e:
    print(f"   [WARN] Embedding API test failed: {str(e)}")
    print(f"   (This is optional, continuing...)")

print("\n" + "=" * 60)
print("ALL CRITICAL TESTS PASSED!")
print("=" * 60)
print("\nReady to build! Moving to implementation phase...")
print("\nTime remaining: ~6 hours")
print("Next: Deploy serverless agentic AI application\n")

