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

def upload_file(data, filename):
    bucket = os.getenv('BUCKET')
    end_url = os.getenv('END_URL')
    s3 = get_s3client()
    print('uploaded filename')
    url = (f'https://api.cloudflare.com/client/v4/accounts/{account_id}>/images/v2/direct_upload')
    response = requests.post(url, params=params, files=files)

    return(end_url + filename)

api_key = os.getenv('IMAGE_API')
account_id = os.getenv('ACCOUNT_ID')
curl --request POST \
curl -X POST \
  "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/images/v1" \
  -H "Authorization: Bearer <API_TOKEN>" \
  -F file=@./<YOUR_IMAGE.IMG>


import ssl
import certifi
from urllib.request import urlopen