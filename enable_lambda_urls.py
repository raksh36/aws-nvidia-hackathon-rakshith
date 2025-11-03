#!/usr/bin/env python3
"""
Enable Lambda Function URLs to expose Lambda functions over HTTPS
This allows the web interface to call them directly
"""
import boto3
import json

AWS_REGION = 'us-east-1'
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

LAMBDA_FUNCTIONS = [
    'logguardian-task-analyzer',
    'logguardian-task-executor',
    'logguardian-retrieval-agent'
]

def enable_function_url(function_name):
    """Enable public Function URL for a Lambda function"""
    try:
        # Check if Function URL already exists
        try:
            response = lambda_client.get_function_url_config(FunctionName=function_name)
            print(f"[OK] {function_name}: Function URL already exists")
            print(f"     URL: {response['FunctionUrl']}")
            return response['FunctionUrl']
        except lambda_client.exceptions.ResourceNotFoundException:
            pass
        
        # Create Function URL
        print(f"[...] {function_name}: Creating Function URL...")
        response = lambda_client.create_function_url_config(
            FunctionName=function_name,
            AuthType='NONE',  # Public access (no auth required)
            Cors={
                'AllowOrigins': ['*'],  # Allow from any origin
                'AllowMethods': ['*'],  # Allow all methods
                'AllowHeaders': ['*'],  # Allow all headers
                'MaxAge': 86400
            }
        )
        
        function_url = response['FunctionUrl']
        print(f"[OK] {function_name}: Function URL created!")
        print(f"     URL: {function_url}")
        
        # Add permission for public invocation
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='FunctionURLAllowPublicAccess',
                Action='lambda:InvokeFunctionUrl',
                Principal='*',
                FunctionUrlAuthType='NONE'
            )
            print(f"[OK] {function_name}: Public access enabled")
        except lambda_client.exceptions.ResourceConflictException:
            print(f"[INFO] {function_name}: Permission already exists")
        
        return function_url
        
    except Exception as e:
        print(f"[ERROR] {function_name}: {str(e)}")
        return None

def main():
    print("=" * 70)
    print("ENABLING LAMBDA FUNCTION URLS")
    print("=" * 70)
    print()
    
    urls = {}
    
    for func_name in LAMBDA_FUNCTIONS:
        url = enable_function_url(func_name)
        if url:
            urls[func_name] = url
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Copy these URLs - you'll need them for the web interface:")
    print()
    for func_name, url in urls.items():
        print(f"{func_name}:")
        print(f"  {url}")
        print()
    
    # Save to config file
    with open('lambda_urls.json', 'w') as f:
        json.dump(urls, f, indent=2)
    print("[OK] URLs saved to lambda_urls.json")
    print()
    print("Next step: Update web/index.html with these URLs!")

if __name__ == '__main__':
    main()

