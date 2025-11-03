#!/usr/bin/env python3
"""
Test Lambda by invoking it directly (not via Function URL)
"""
import boto3
import json

AWS_REGION = 'us-east-1'
lambda_client = boto3.client('lambda', region_name=AWS_REGION)

print("=" * 70)
print("TESTING LAMBDA DIRECT INVOCATION")
print("=" * 70)
print()

test_event = {
    'body': json.dumps({'user_request': 'Test request'})
}

print("Invoking Lambda directly...")
response = lambda_client.invoke(
    FunctionName='logguardian-task-analyzer',
    InvocationType='RequestResponse',
    Payload=json.dumps(test_event)
)

status_code = response['StatusCode']
payload = json.loads(response['Payload'].read())

print(f"Status Code: {status_code}")
print(f"Response:")
print(json.dumps(payload, indent=2))

if status_code == 200:
    print()
    print("[SUCCESS] Lambda works when invoked directly!")
    print()
    print("The problem is with the Lambda Function URL configuration.")
else:
    print()
    print("[ERROR] Lambda failed even with direct invocation")

