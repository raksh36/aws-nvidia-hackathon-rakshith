"""
Task Analyzer Agent - SageMaker Version
Uses NVIDIA LLM via Amazon SageMaker endpoint
"""
import json
import boto3
import time
from decimal import Decimal

# Configuration
SAGEMAKER_LLM_ENDPOINT = 'logguardian-llm-endpoint'
TABLE_TASKS = 'logguardian-tasks'
TABLE_AGENT_MEMORY = 'logguardian-agent-memory'

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
tasks_table = dynamodb.Table(TABLE_TASKS)
memory_table = dynamodb.Table(TABLE_AGENT_MEMORY)

def call_sagemaker_llm(messages, max_tokens=500, temperature=0.7):
    """Call SageMaker endpoint for LLM reasoning"""
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_LLM_ENDPOINT,
        ContentType='application/json',
        Body=json.dumps(payload)
    )
    
    result = json.loads(response['Body'].read())
    return result['choices'][0]['message']['content']

def analyze_task(user_request):
    """Analyze user request and generate task breakdown"""
    
    system_prompt = """You are an intelligent task analysis agent. Your job is to:
1. Understand the user's request
2. Break it down into specific, actionable subtasks
3. Determine the priority and dependencies
4. Return a structured analysis

Respond in JSON format:
{
  "task_summary": "Brief summary",
  "subtasks": [
    {
      "id": 1,
      "action": "Specific action to take",
      "priority": "high|medium|low",
      "estimated_time": "estimated time in minutes"
    }
  ],
  "reasoning": "Your step-by-step reasoning"
}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this request: {user_request}"}
    ]
    
    # Get LLM analysis via SageMaker
    llm_response = call_sagemaker_llm(messages, max_tokens=800, temperature=0.3)
    
    # Parse JSON response
    try:
        if "```json" in llm_response:
            json_str = llm_response.split("```json")[1].split("```")[0].strip()
        elif "```" in llm_response:
            json_str = llm_response.split("```")[1].split("```")[0].strip()
        else:
            json_str = llm_response.strip()
        
        analysis = json.loads(json_str)
        return analysis
    except json.JSONDecodeError:
        return {
            "task_summary": user_request,
            "subtasks": [
                {
                    "id": 1,
                    "action": user_request,
                    "priority": "medium",
                    "estimated_time": "5"
                }
            ],
            "reasoning": "Direct execution of user request"
        }

def store_task(task_id, analysis, user_request):
    """Store analyzed task in DynamoDB"""
    def convert_floats(obj):
        if isinstance(obj, dict):
            return {k: convert_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(item) for item in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        return obj
    
    task_item = {
        'task_id': task_id,
        'user_request': user_request,
        'analysis': convert_floats(analysis),
        'status': 'pending',
        'created_at': int(time.time()),
        'updated_at': int(time.time())
    }
    
    tasks_table.put_item(Item=task_item)
    return task_item

def lambda_handler(event, context):
    """Lambda handler for Task Analyzer Agent"""
    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        user_request = body.get('user_request', '')
        
        if not user_request:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'user_request is required'})
            }
        
        task_id = f"task-{int(time.time())}-{hash(user_request) % 10000:04d}"
        
        print(f"[TASK ANALYZER] Processing: {user_request}")
        
        # Analyze via SageMaker
        analysis = analyze_task(user_request)
        print(f"[TASK ANALYZER] Analysis complete: {len(analysis.get('subtasks', []))} subtasks")
        
        task_item = store_task(task_id, analysis, user_request)
        print(f"[TASK ANALYZER] Task stored: {task_id}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'task_id': task_id,
                'analysis': analysis,
                'status': 'analyzed',
                'message': f"Task analyzed into {len(analysis.get('subtasks', []))} subtasks"
            })
        }
        
    except Exception as e:
        print(f"[ERROR] Task Analyzer failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

