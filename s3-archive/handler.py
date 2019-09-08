import json
import boto3
import os
from iptcinfo3 import IPTCInfo
from PIL import Image
from PIL.ExifTags import TAGS
import mac_tag


paths = [
    '/Users/david/Downloads/20090509131026_botanic_001.jpeg',
    '/Users/david/Pictures/20190705italy/DSC_0461.NEF'
]

def get_labeled_exif(exif):
    labeled = {}
    for (key, val) in exif.items():
        labeled[TAGS.get(key)] = val
    return labeled

def get_exif(filename):
    image = Image.open(filename)
    image.verify()
    return image._getexif()

def get_user_comment(path):
    try:
        # info = IPTCInfo(
        exif = get_exif(path)
        labeled = get_labeled_exif(exif)
        return labeled['UserComment'].decode("utf-8")
    except:
        return False

def get_osx_tags(path):
    return mac_tag.get([path])

def test():
    for path in paths:
        print(path)
        user_comment = get_user_comment(path)
        print(user_comment)
        osx_tags = get_osx_tags(path)

def ingest(event, context):
    path = '20090509botanicgarden/20090509131026_botanic_001.JPG'
    client = boto3.client('s3')
    response = client.get_object(
        Bucket=os.environ['BUCKET'],
        Key=path
    )
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

test()
