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


import requests

url = "https://api.cloudflare.com/client/v4/accounts/245302718047bba4dfecc0817e7c92b1/images/v1"

payload = '-----011000010111000001101001\r\nContent-Disposition: form-data; name="metadata"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name="requireSignedURLs"\r\n\r\n\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name="url"\r\n\r\n["https://media.ecotoxicologylab.com/bahud16_1219.jpg"]\r\n-----011000010111000001101001--\r\n\r\n'
headers = {
    "Content-Type": "multipart/form-data; boundary=---011000010111000001101001",
    "Authorization": "Bearer 0OvtGq80fSxAkZ6Ruh4BWwsL6D2oEEgc"
}

response = requests.request("POST", url, data=payload, headers=headers)

print(response.text)



import requests

headers = {
    'Authorization': 'Bearer 462XIN0OdrHu6k3MkbYoNu5mACi3GJkRW6OQtT7B',
}

files = {
    'file': open('./bahud22.jpg', 'rb'),
}
response = requests.post('https://api.cloudflare.com/client/v4/accounts/245302718047bba4dfecc0817e7c92b1/images/v1', headers=headers, files=files)



import ssl
import certifi
from urllib.request import urlopen