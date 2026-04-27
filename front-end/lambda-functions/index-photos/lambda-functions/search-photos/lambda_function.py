import json
import boto3
import urllib3
import base64

OPENSEARCH_ENDPOINT = 'search-photos-lvpdk6j3nrcjyzqgqnyq2vemwe.aos.us-east-1.on.aws'
OPENSEARCH_USER = 'admin'
OPENSEARCH_PASS = 'Admin123!'

lex = boto3.client('lexv2-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    print(str(event))
    params = event.get('queryStringParameters') or {}
    query = params.get('q', '')
    print('Query: ' + query)
    if not query:
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'results': []})
        }
    lex_response = lex.recognize_text(
        botId='4EPLANJOWR',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId='session1',
        text=query
    )
    keywords = []
    slots = lex_response.get('sessionState', {}).get('intent', {}).get('slots', {})
    for slot_name, slot_value in slots.items():
        if slot_value and slot_value.get('value', {}).get('interpretedValue'):
            keywords.append(slot_value['value']['interpretedValue'].lower())
    print('Keywords: ' + str(keywords))
    if not keywords:
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'results': []})
        }
    http = urllib3.PoolManager()
    credentials = base64.b64encode((OPENSEARCH_USER + ':' + OPENSEARCH_PASS).encode()).decode()
    search_query = {'query': {'terms': {'labels': keywords}}}
    response = http.request(
        'GET',
        'https://' + OPENSEARCH_ENDPOINT + '/photos/_search',
        body=json.dumps(search_query).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + credentials
        }
    )
    results = json.loads(response.data.decode())
    photos = []
    for hit in results.get('hits', {}).get('hits', []):
        source = hit['_source']
        photos.append({
            'url': 'https://' + source['bucket'] + '.s3.amazonaws.com/' + source['objectKey'],
            'labels': source['labels']
        })
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'results': photos})
    }
