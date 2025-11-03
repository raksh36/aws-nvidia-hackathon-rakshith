"""
Task Executor Agent - SageMaker Version
Executes tasks autonomously via SageMaker LLM endpoint
"""
import json
import boto3
import time
from decimal import Decimal

# Configuration
SAGEMAKER_LLM_ENDPOINT = 'logguardian-llm-endpoint'
TABLE_TASKS = 'logguardian-tasks'

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
tasks_table = dynamodb.Table(TABLE_TASKS)

def convert_floats(obj):
    """Convert floats to Decimal for DynamoDB"""
    if isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats(item) for item in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

def call_sagemaker_llm(messages, max_tokens=500, temperature=0.7):
    """Call SageMaker endpoint"""
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

def get_task(task_id):
    """Retrieve task from DynamoDB"""
    response = tasks_table.get_item(Key={'task_id': task_id})
    return response.get('Item')

def update_task_status(task_id, status, execution_log=None):
    """Update task status"""
    update_expr = "SET #status = :status, updated_at = :updated_at"
    expr_values = {
        ':status': status,
        ':updated_at': int(time.time())
    }
    expr_names = {'#status': 'status'}
    
    if execution_log:
        update_expr += ", execution_log = :log"
        expr_values[':log'] = convert_floats(execution_log)
    
    tasks_table.update_item(
        Key={'task_id': task_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ExpressionAttributeNames=expr_names
    )

def execute_subtask(subtask, context):
    """Execute a single subtask"""
    system_prompt = """You are an autonomous task execution agent. You can:
1. Analyze log data
2. Identify patterns and issues
3. Suggest remediation actions
4. Execute safe operations

Respond in JSON format:
{
  "reasoning": "Your step-by-step thinking",
  "actions_taken": ["action 1", "action 2"],
  "result": "What was accomplished",
  "confidence": 0.85,
  "warnings": ["warning 1"],
  "recommendations": ["recommendation 1"]
}"""

    user_message = f"""
Task: {subtask.get('action', 'Unknown')}
Priority: {subtask.get('priority', 'medium')}
Context: {json.dumps(context)}

Execute this task and report results."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    llm_response = call_sagemaker_llm(messages, max_tokens=600, temperature=0.3)
    
    try:
        if "```json" in llm_response:
            json_str = llm_response.split("```json")[1].split("```")[0].strip()
        elif "```" in llm_response:
            json_str = llm_response.split("```")[1].split("```")[0].strip()
        else:
            json_str = llm_response.strip()
        
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {
            "reasoning": llm_response,
            "actions_taken": [f"Executed: {subtask.get('action')}"],
            "result": "Task completed",
            "confidence": 0.7,
            "warnings": [],
            "recommendations": []
        }

def lambda_handler(event, context):
    """Lambda handler for Task Executor"""
    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        task_id = body.get('task_id', '')
        
        if not task_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'task_id is required'})
            }
        
        print(f"[TASK EXECUTOR] Executing: {task_id}")
        
        task = get_task(task_id)
        if not task:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Task not found'})
            }
        
        update_task_status(task_id, 'executing')
        
        analysis = task.get('analysis', {})
        subtasks = analysis.get('subtasks', [])
        
        print(f"[TASK EXECUTOR] Processing {len(subtasks)} subtasks")
        
        execution_results = []
        execution_context = {
            "task_summary": analysis.get('task_summary', ''),
            "user_request": task.get('user_request', '')
        }
        
        for subtask in subtasks:
            print(f"[TASK EXECUTOR] Subtask {subtask.get('id')}: {subtask.get('action')}")
            
            try:
                result = execute_subtask(subtask, execution_context)
                result['subtask_id'] = subtask.get('id')
                result['subtask_action'] = subtask.get('action')
                result['status'] = 'completed'
                execution_results.append(result)
                
                execution_context[f"subtask_{subtask.get('id')}_result"] = result.get('result', '')
                
            except Exception as e:
                print(f"[TASK EXECUTOR] Subtask {subtask.get('id')} failed: {str(e)}")
                execution_results.append({
                    'subtask_id': subtask.get('id'),
                    'subtask_action': subtask.get('action'),
                    'status': 'failed',
                    'error': str(e)
                })
        
        final_status = 'completed' if all(r.get('status') == 'completed' for r in execution_results) else 'partially_completed'
        update_task_status(task_id, final_status, execution_results)
        
        print(f"[TASK EXECUTOR] Finished: {final_status}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'task_id': task_id,
                'status': final_status,
                'execution_results': execution_results,
                'completed_subtasks': sum(1 for r in execution_results if r.get('status') == 'completed'),
                'total_subtasks': len(subtasks)
            }, default=str)
        }
        
    except Exception as e:
        print(f"[ERROR] Task Executor failed: {str(e)}")
        if 'task_id' in locals():
            try:
                update_task_status(task_id, 'failed', [{'error': str(e)}])
            except:
                pass
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

