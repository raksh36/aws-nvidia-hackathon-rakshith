"""
Minimal Lambda test - just return success
"""
import json

def lambda_handler(event, context):
    """Minimal test handler"""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Hello from Lambda!', 'event': str(event)[:200]})
    }

