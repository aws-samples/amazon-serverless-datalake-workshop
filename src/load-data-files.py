import boto3
import random
import string
import uuid
import httplib
import urlparse
import json
import base64
import hashlib
import os

s3_client = boto3.client('s3')
s3 = boto3.resource('s3')

def lambda_handler(event, context):
    try:
        print("event", event)
        return process_cfn(event, context)
    except Exception as e:
        print("EXCEPTION", e)
        print(e)
        send_response(event, {
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId']
            }, "FAILED")

def delete_files(event, content):
    bucket = os.environ['BUCKET_NAME']
    marker = ''
    maxKeys = 100

    isTruncated = True
    s3_bucket = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=maxKeys)

    while isTruncated:
        isTruncated = s3_bucket['IsTruncated']
        
        objects = []

        for obj in s3_bucket['Contents'] :
            objects.append({"Key": obj["Key"]})


        response = s3_client.delete_objects(
            Bucket=bucket,
            Delete={
                'Objects': objects,
                'Quiet': True
            }
        )

        if isTruncated:
            marker = s3_bucket['NextContinuationToken']
            s3_bucket = s3_client.list_objects_v2(Bucket=bucket, ContinuationToken=marker, MaxKeys=maxKeys)

    return "Success"



def process_cfn(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    bucket = os.environ['BUCKET_NAME']

    response = {
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Status': 'IN_PROCESS',
    }

    if event['RequestType'] == 'Delete':
        delete_files(event, context)
        return send_response(event, response, status="SUCCESS", reason="Deleted")
         
    copy_files(event, context)
    return send_response(event, response, status="SUCCESS", reason="Files Updated")


def copy_files(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    stackName =  event['ResourceProperties']['StackName']

    bucket = os.environ['BUCKET_NAME']
    sourceBucket = os.environ['SOURCE_BUCKET_NAME']

    response = s3_client.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': 'arc326-instructions', 'Key': 'sample-data/useractivity.csv'},
        Key='raw/useractivity/useractivity.csv'
    )

    response = s3_client.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': 'arc326-instructions', 'Key': 'sample-data/zipcodedata.csv'},
        Key='raw/zipcodes/zipcodedata.csv'
    )

    response = s3_client.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': 'arc326-instructions', 'Key': 'sample-data/userprofile.csv'},
        Key='raw/userprofile/userprofile.csv'
    )

    src = s3.Object(sourceBucket, 'instructions/instructions-template.html')
    html = src.get()['Body'].read().decode('utf-8') 

    html = html.replace('^ingestionbucket^', bucket)
    html = html.replace('^stackname^', stackName)

    destination = s3.Object(bucket, 'instructions/instructions.html')
    result = destination.put(Body=html, ACL='public-read', ContentDisposition='inline', ContentType='text/html')


    return "Success"

def send_response(request, response, status=None, reason=None):
    if status is not None:
        response['Status'] = status

    if reason is not None:
        response['Reason'] = reason

    if not 'PhysicalResourceId' in response or response['PhysicalResourceId']:
        response['PhysicalResourceId'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))


    if not 'ResponseURL' in request or request['ResponseURL'] == '':
            s3params = {"Bucket": 'gillemi-gillemi', "Key": 'result.json'}
            request['ResponseURL'] = s3_client.generate_presigned_url('put_object', s3params)
            print('The debug URL is', request['ResponseURL'])

    if 'ResponseURL' in request and request['ResponseURL']:
        url = urlparse.urlparse(request['ResponseURL'])
        body = json.dumps(response)
        print ('body', url, body)
        https = httplib.HTTPSConnection(url.hostname)
        https.request('PUT', url.path+'?'+url.query, body)

    return response

