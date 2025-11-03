#!/usr/bin/env python3
"""
Setup DynamoDB tables for AgentOps
"""
import os
import sys
import boto3
from config import AWS_REGION, TABLE_TASKS, TABLE_AGENT_MEMORY, TABLE_CONVERSATIONS

# Credentials from environment variables

dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)

def create_table_if_not_exists(table_name, key_schema, attribute_definitions, billing_mode='PAY_PER_REQUEST'):
    """Create DynamoDB table if it doesn't exist"""
    try:
        # Check if table exists
        dynamodb.describe_table(TableName=table_name)
        print(f"[EXISTS] Table {table_name} already exists")
        return True
    except dynamodb.exceptions.ResourceNotFoundException:
        # Create table
        print(f"[CREATE] Creating table {table_name}...")
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode=billing_mode
        )
        
        # Wait for table to be created
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"[OK] Table {table_name} created successfully!")
        return True
    except Exception as e:
        print(f"[FAIL] Error with table {table_name}: {str(e)}")
        return False

print("=" * 60)
print("DYNAMODB SETUP - AgentOps")
print("=" * 60)

# Table 1: Tasks (for agentic task management)
print("\n[1/3] Tasks table...")
success1 = create_table_if_not_exists(
    table_name=TABLE_TASKS,
    key_schema=[
        {'AttributeName': 'task_id', 'KeyType': 'HASH'},
    ],
    attribute_definitions=[
        {'AttributeName': 'task_id', 'AttributeType': 'S'},
    ]
)

# Table 2: Agent Memory (for storing agent knowledge and context)
print("\n[2/3] Agent Memory table...")
success2 = create_table_if_not_exists(
    table_name=TABLE_AGENT_MEMORY,
    key_schema=[
        {'AttributeName': 'memory_id', 'KeyType': 'HASH'},
    ],
    attribute_definitions=[
        {'AttributeName': 'memory_id', 'AttributeType': 'S'},
    ]
)

# Table 3: Conversations (for storing conversation history)
print("\n[3/3] Conversations table...")
success3 = create_table_if_not_exists(
    table_name=TABLE_CONVERSATIONS,
    key_schema=[
        {'AttributeName': 'conversation_id', 'KeyType': 'HASH'},
        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'},
    ],
    attribute_definitions=[
        {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
        {'AttributeName': 'timestamp', 'AttributeType': 'N'},
    ]
)

print("\n" + "=" * 60)
if success1 and success2 and success3:
    print("ALL TABLES READY!")
    print("=" * 60)
    print("\nNext: Deploy Lambda functions")
    sys.exit(0)
else:
    print("SOME TABLES FAILED!")
    print("=" * 60)
    sys.exit(1)

