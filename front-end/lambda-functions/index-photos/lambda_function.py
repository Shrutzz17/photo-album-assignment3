import json
import boto3
import urllib.parse
from datetime import datetime
import urllib3
import base64

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')

OPENSEARCH_ENDPOINT = 'search-photos-lvpdk6j3nrcjyzqgqnyq2vemwe.aos.us-east-1.on.aws'
OPENSEARCH_USER = 'admin'
OPENSEARCH_PASS = 'Admin123!'

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    rekognition_response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MaxLabels=10
    )
    labels = [label['Name'].lower() for label in rekognition_response['Labels']]
    metadata = s3.head_object(Bucket=bucket, Key=key)
    custom_labels = metadata.get('Metadata', {}).get('customlabels', '')
    if custom_labels:
        labels += [l.strip().lower() for l in custom_labels.split(',')]
    doc = {
        'objectKey': key,
        'bucket': bucket,
        'createdTimestamp': datetime.now().isoformat(),
        'labels': labels
    }
    print('Indexing: ' + key + ' with labels: ' + str(labels))
    http = urllib3.PoolManager()
    credentials = base64.b64encode((OPENSEARCH_USER + ':' + OPENSEARCH_PASS).encode()).decode()
    response = http.request(
        'POST',
        'https://' + OPENSEARCH_ENDPOINT + '/photos/_doc',
        body=json.dumps(doc).encode(),
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + credentials
        }
    )
    print('OpenSearch response: ' + str(response.status))
    return {'statusCode': 200, 'body': 'Done'}
