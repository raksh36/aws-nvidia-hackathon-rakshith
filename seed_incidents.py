#!/usr/bin/env python3
"""
Seed sample incident data for Retrieval Agent to use
"""
import requests
import json

RETRIEVAL_AGENT_URL = 'https://m43tfjdq5sik2s4uxxi7m3khwq0jfpht.lambda-url.us-east-1.on.aws/'

# Sample past incidents for the knowledge base
SAMPLE_INCIDENTS = [
    {
        "text": "Database experiencing high CPU usage and slow query performance due to missing indexes",
        "metadata": {
            "summary": "Database performance degradation - missing indexes",
            "solution": "Added indexes on frequently queried columns, optimized slow queries, CPU usage dropped from 95% to 25%",
            "severity": "high",
            "category": "database",
            "resolved_time": "45 minutes"
        }
    },
    {
        "text": "API returning 500 errors with increased latency due to connection pool exhaustion",
        "metadata": {
            "summary": "API 500 errors - connection pool exhaustion",
            "solution": "Increased database connection pool size from 10 to 50, implemented connection timeout, errors resolved",
            "severity": "critical",
            "category": "api",
            "resolved_time": "30 minutes"
        }
    },
    {
        "text": "Memory leak in microservice causing OOM errors and pod restarts",
        "metadata": {
            "summary": "Memory leak causing OOM crashes",
            "solution": "Identified unclosed database connections, added proper connection cleanup in finally blocks, memory stable",
            "severity": "high",
            "category": "memory",
            "resolved_time": "2 hours"
        }
    },
    {
        "text": "Unusual authentication attempts from multiple IPs - potential brute force attack",
        "metadata": {
            "summary": "Brute force authentication attack detected",
            "solution": "Implemented rate limiting on login endpoint, blocked suspicious IPs, enabled 2FA for affected accounts",
            "severity": "critical",
            "category": "security",
            "resolved_time": "20 minutes"
        }
    },
    {
        "text": "Kubernetes pods failing to start due to insufficient memory resources",
        "metadata": {
            "summary": "Pod scheduling failures - resource constraints",
            "solution": "Scaled up node pool, adjusted pod memory requests/limits, implemented horizontal pod autoscaling",
            "severity": "medium",
            "category": "kubernetes",
            "resolved_time": "1 hour"
        }
    },
    {
        "text": "Network timeout between services causing request failures",
        "metadata": {
            "summary": "Inter-service network timeouts",
            "solution": "Identified network policy blocking traffic, updated security group rules, implemented retry logic with backoff",
            "severity": "high",
            "category": "network",
            "resolved_time": "40 minutes"
        }
    },
    {
        "text": "Application logs showing repeated OutOfMemoryError in payment service",
        "metadata": {
            "summary": "Payment service memory exhaustion",
            "solution": "Increased JVM heap size, fixed memory leak in cache implementation, added monitoring alerts",
            "severity": "critical",
            "category": "memory",
            "resolved_time": "90 minutes"
        }
    },
    {
        "text": "Auto-scaling not triggering despite high CPU load on EC2 instances",
        "metadata": {
            "summary": "Auto-scaling policy not working",
            "solution": "Fixed CloudWatch alarm threshold, updated scaling policy cooldown period, verified IAM permissions",
            "severity": "medium",
            "category": "infrastructure",
            "resolved_time": "25 minutes"
        }
    },
    {
        "text": "Database connection errors after deployment - connection string misconfiguration",
        "metadata": {
            "summary": "Post-deployment database connection failures",
            "solution": "Rolled back deployment, fixed connection string in environment variables, redeployed successfully",
            "severity": "critical",
            "category": "deployment",
            "resolved_time": "15 minutes"
        }
    },
    {
        "text": "Elasticsearch cluster yellow status due to unassigned shards",
        "metadata": {
            "summary": "Elasticsearch cluster health degraded",
            "solution": "Increased cluster size, redistributed shards, enabled shard allocation, cluster returned to green status",
            "severity": "medium",
            "category": "database",
            "resolved_time": "50 minutes"
        }
    }
]

print("=" * 70)
print("SEEDING INCIDENT DATA TO RETRIEVAL AGENT")
print("=" * 70)
print()

success_count = 0
total = len(SAMPLE_INCIDENTS)

for i, incident in enumerate(SAMPLE_INCIDENTS, 1):
    print(f"[{i}/{total}] Storing: {incident['metadata']['summary'][:50]}...")
    
    try:
        response = requests.post(
            RETRIEVAL_AGENT_URL,
            headers={'Content-Type': 'application/json'},
            json={
                'action': 'store',
                'text': incident['text'],
                'metadata': incident['metadata']
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"         [OK] Stored successfully")
            success_count += 1
        else:
            print(f"         [FAIL] Status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"         [ERROR] {str(e)}")

print()
print("=" * 70)
print(f"SEEDING COMPLETE: {success_count}/{total} incidents stored")
print("=" * 70)
print()

if success_count > 0:
    print("Retrieval Agent now has knowledge base!")
    print("The Task Executor will use these incidents for context.")
else:
    print("WARNING: No incidents were stored successfully")
    print("Check the Retrieval Agent Lambda logs for errors")

