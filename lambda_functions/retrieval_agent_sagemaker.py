"""
Retrieval Agent - SageMaker Version
Uses NVIDIA Embeddings via Amazon SageMaker endpoint
"""
import json
import boto3
import time
from decimal import Decimal
import math

# Configuration
SAGEMAKER_EMBED_ENDPOINT = 'logguardian-embed-endpoint'
TABLE_AGENT_MEMORY = 'logguardian-agent-memory'

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-east-1')
memory_table = dynamodb.Table(TABLE_AGENT_MEMORY)

def get_embedding(text, input_type='query'):
    """Get embedding vector from SageMaker endpoint"""
    payload = {
        "input": text,
        "input_type": input_type
    }
    
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName=SAGEMAKER_EMBED_ENDPOINT,
        ContentType='application/json',
        Body=json.dumps(payload)
    )
    
    result = json.loads(response['Body'].read())
    return result['data'][0]['embedding']

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

def store_memory(memory_text, metadata=None):
    """Store a new memory with embedding"""
    memory_id = f"mem-{int(time.time())}-{hash(memory_text) % 10000:04d}"
    
    embedding = get_embedding(memory_text, input_type='passage')
    embedding_decimal = [Decimal(str(x)) for x in embedding]
    
    memory_item = {
        'memory_id': memory_id,
        'text': memory_text,
        'embedding': embedding_decimal,
        'metadata': metadata or {},
        'created_at': int(time.time())
    }
    
    memory_table.put_item(Item=memory_item)
    return memory_id

def search_similar_memories(query_text, top_k=5):
    """Search for similar memories"""
    query_embedding = get_embedding(query_text, input_type='query')
    
    response = memory_table.scan()
    memories = response.get('Items', [])
    
    results = []
    for memory in memories:
        if 'embedding' in memory:
            memory_embedding = [float(x) for x in memory['embedding']]
            similarity = cosine_similarity(query_embedding, memory_embedding)
            
            results.append({
                'memory_id': memory['memory_id'],
                'text': memory['text'],
                'similarity': similarity,
                'metadata': memory.get('metadata', {}),
                'created_at': memory.get('created_at', 0)
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]

def lambda_handler(event, context):
    """Lambda handler for Retrieval Agent"""
    try:
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event
        
        action = body.get('action', 'search')
        text = body.get('text', '')
        
        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'text is required'})
            }
        
        if action == 'store':
            metadata = body.get('metadata', {})
            memory_id = store_memory(text, metadata)
            
            print(f"[RETRIEVAL AGENT] Stored memory: {memory_id}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'memory_id': memory_id,
                    'status': 'stored',
                    'message': 'Memory stored successfully'
                })
            }
            
        elif action == 'search':
            top_k = body.get('top_k', 5)
            results = search_similar_memories(text, top_k)
            
            print(f"[RETRIEVAL AGENT] Found {len(results)} similar memories")
            
            def convert_decimals(obj):
                if isinstance(obj, list):
                    return [convert_decimals(i) for i in obj]
                elif isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, Decimal):
                    return float(obj)
                return obj
            
            results_converted = convert_decimals(results)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'results': results_converted,
                    'count': len(results),
                    'query': text
                })
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'action must be "store" or "search"'})
            }
        
    except Exception as e:
        print(f"[ERROR] Retrieval Agent failed: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

