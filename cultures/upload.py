from dotenv import load_dotenv
import os
import boto3
import time

load_dotenv()


def get_s3client():
    bucketurl = os.getenv('BUCKETURL')
    access_key = os.getenv('ACCESSKEYID'),
    key_secret = os.getenv('ACCESS_KEY_SECRET')
    s3 = boto3.client('s3',
      region_name="auto",
      endpoint_url = bucketurl,
      aws_access_key_id = access_key,
      aws_secret_access_key = key_secret,
      verify=False
       )
    return s3

def upload_pdf(filename):
    s3 = get_s3client()
    with open('20230210labels.pdf', 'rb') as data:
        s3.upload_fileobj(data, os.getenv('BUCKET'), '20230210labels.pdf')
        print('uploaded filename')
    return('success')
