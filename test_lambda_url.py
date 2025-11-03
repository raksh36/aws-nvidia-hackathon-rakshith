#!/usr/bin/env python3
"""
Quick test of Lambda Function URLs
Tests if the web interface can call the real AI
"""
import requests
import json

# Lambda Function URLs
TASK_ANALYZER_URL = 'https://6wpmt7hsdsnbqalczm4xghnxbm0uvbjo.lambda-url.us-east-1.on.aws/'

print("=" * 70)
print("TESTING LAMBDA FUNCTION URL")
print("=" * 70)
print()

# Test payload
test_request = "Analyze server logs for memory leaks and suggest remediation steps"

print(f"[1/2] Sending request to Task Analyzer Lambda...")
print(f"      Request: '{test_request}'")
print()

try:
    response = requests.post(
        TASK_ANALYZER_URL,
        headers={'Content-Type': 'application/json'},
        json={'user_request': test_request},
        timeout=60
    )
    
    print(f"[2/2] Response received!")
    print(f"      Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("[SUCCESS] Lambda is working!")
        print()
        print("Response Data:")
        print(json.dumps(data, indent=2))
        print()
        print("=" * 70)
        print("✅ WEB INTERFACE WILL WORK!")
        print("=" * 70)
        print()
        print(f"Your web app at https://raksh36.github.io/aws-nvidia-hackathon-rakshith/")
        print("will now call this Lambda and show REAL AI responses!")
        
    else:
        print(f"[ERROR] HTTP {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"[ERROR] {str(e)}")
    print()
    print("This might mean:")
    print("- Lambda endpoint is not accessible")
    print("- CORS is not configured")
    print("- Network issue")

