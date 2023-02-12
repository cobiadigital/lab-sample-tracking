from dotenv import load_dotenv
import os
import boto3
import time

load_dotenv()


def get_s3client():
    url = os.getenv('URL')
    access_key = os.getenv('ACCESS_KEY_ID')
    key_secret = os.getenv('KEY_SECRET')

    s3 = boto3.client('s3',
      region_name="auto",
      endpoint_url = url,
      aws_access_key_id = access_key,
      aws_secret_access_key = key_secret,
       )
    return s3

def upload_pdf(data, filename):
    bucket = os.getenv('BUCKET')
    end_url = os.getenv('END_URL')
    s3 = get_s3client()
    s3.upload_fileobj(data, bucket, filename)
    print('uploaded filename')
    return(end_url + filename)
