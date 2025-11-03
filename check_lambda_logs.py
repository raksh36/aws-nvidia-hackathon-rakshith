#!/usr/bin/env python3
"""
Check recent Lambda logs to debug 502 error
"""
import boto3
import time
from datetime import datetime, timedelta

AWS_REGION = 'us-east-1'
logs_client = boto3.client('logs', region_name=AWS_REGION)

FUNCTION_NAME = 'logguardian-task-analyzer'
LOG_GROUP = f'/aws/lambda/{FUNCTION_NAME}'

print("=" * 70)
print(f"CHECKING LAMBDA LOGS: {FUNCTION_NAME}")
print("=" * 70)
print()

try:
    # Get recent logs (last 5 minutes)
    start_time = int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000)
    end_time = int(datetime.now().timestamp() * 1000)
    
    print(f"Fetching logs from last 5 minutes...")
    print()
    
    response = logs_client.filter_log_events(
        logGroupName=LOG_GROUP,
        startTime=start_time,
        endTime=end_time,
        limit=50
    )
    
    events = response.get('events', [])
    
    if not events:
        print("[INFO] No recent logs found")
        print()
        print("This might mean:")
        print("- Lambda hasn't been called recently")
        print("- Logs are delayed")
        print()
    else:
        print(f"Found {len(events)} log entries:")
        print()
        
        for event in events[-20:]:  # Last 20 entries
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message'].strip()
            
            # Highlight errors
            if 'ERROR' in message or 'Error' in message or 'error' in message:
                print(f"[{timestamp.strftime('%H:%M:%S')}] ⚠️  {message}")
            elif '[TASK ANALYZER]' in message:
                print(f"[{timestamp.strftime('%H:%M:%S')}] ✓  {message}")
            else:
                print(f"[{timestamp.strftime('%H:%M:%S')}]    {message}")
    
    print()
    print("=" * 70)
    print("To see full logs, go to:")
    print(f"https://console.aws.amazon.com/cloudwatch/home?region={AWS_REGION}#logsV2:log-groups/log-group/{LOG_GROUP.replace('/', '$252F')}")
    
except logs_client.exceptions.ResourceNotFoundException:
    print(f"[ERROR] Log group not found: {LOG_GROUP}")
    print()
    print("This means the Lambda hasn't been invoked yet or logs aren't enabled.")
    
except Exception as e:
    print(f"[ERROR] Failed to fetch logs: {str(e)}")

