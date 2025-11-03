#!/usr/bin/env python3
"""
Test Task Executor Lambda to debug 500 error
"""
import requests
import json

TASK_EXECUTOR_URL = 'https://oo24hbvhsmhgg24tbjcgsk57ly0xgftt.lambda-url.us-east-1.on.aws/'

# First, create a task with the analyzer
TASK_ANALYZER_URL = 'https://6wpmt7hsdsnbqalczm4xghnxbm0uvbjo.lambda-url.us-east-1.on.aws/'

print("=" * 70)
print("TESTING TASK EXECUTOR")
print("=" * 70)
print()

# Step 1: Create a task
print("[1/2] Creating a task with Task Analyzer...")
response1 = requests.post(
    TASK_ANALYZER_URL,
    headers={'Content-Type': 'application/json'},
    json={'user_request': 'Simple test task'},
    timeout=30
)

if response1.status_code != 200:
    print(f"[ERROR] Task Analyzer failed: {response1.status_code}")
    print(response1.text)
    exit(1)

data1 = response1.json()
task_id = data1['task_id']
print(f"[OK] Task created: {task_id}")
print()

# Step 2: Execute the task
print(f"[2/2] Executing task {task_id}...")
response2 = requests.post(
    TASK_EXECUTOR_URL,
    headers={'Content-Type': 'application/json'},
    json={'task_id': task_id},
    timeout=60
)

print(f"Status Code: {response2.status_code}")
print()

if response2.status_code == 200:
    data2 = response2.json()
    print("[SUCCESS] Task Executor works!")
    print()
    print("Response:")
    print(json.dumps(data2, indent=2))
else:
    print(f"[ERROR] Task Executor failed: {response2.status_code}")
    print()
    print("Response:")
    print(response2.text)
    print()
    print("Possible causes:")
    print("- Lambda code error")
    print("- DynamoDB access issue")
    print("- SageMaker endpoint error")
    print("- Missing dependencies")

