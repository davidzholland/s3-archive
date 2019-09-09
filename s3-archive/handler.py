import json
import boto3
import os
from iptcinfo3 import IPTCInfo
from PIL import Image
from PIL.ExifTags import TAGS
import mac_tag
from libxmp.utils import file_to_dict
from libxmp import XMPFiles, consts


paths = [
    # TODO: accept paths as input
]

def get_labeled_exif(exif):
    labeled = {}
    for (key, val) in exif.items():
        labeled[TAGS.get(key)] = val
    return labeled

def get_exif(filename):
    try:        
        image = Image.open(filename)
        image.verify()
        exif = image._getexif()
        labeled = get_labeled_exif(exif)
        return labeled
    except:
        return False

def get_xmp(path):
    try:
        data = {}
        xmp = file_to_dict(file_path=path)
        if consts.XMP_NS_DC not in xmp:
            return False
        dc = xmp[consts.XMP_NS_DC]
        for dc_item in dc:
            if dc_item[0][-1] == ']':
                key = dc_item[0].split('[')[0]
                key = key.split(':')[1]
                value = dc_item[1]
                # print('key: ' + key)
                # print('value: ' + value)
                if key in data:
                    if isinstance(data[key], list) == False:
                        previous_value = data[key]
                        data[key] = []
                        data[key].append(previous_value)
                    data[key].append(value)
                else:
                    data[key] = dc_item[1]
        return data
    except Exception as e:
        print('exeption: ', e)
        return False

def get_iptc(path):
    try:
        return IPTCInfo(path, force=True)
    except Exception as e:
        print('exeption: ', e)
        return False

def get_osx_tags(path):
    try:
        tags = mac_tag.get([path])
        return tags[path]
    except Exception as e:
        print('exeption: ', e)
        return False

def parse_metadata():
    items = []
    for path in paths:
        item = {
            'file_path': path,
            'created_at': None,
            'headline': None,
            'caption': None,
            'tags': None,
            'latitude': None,
            'longitude': None
        } 
        # XMP
        xmp = get_xmp(path)
        if xmp:
            if 'description' in xmp:
                item['caption'] = xmp['description']
        # EXIF
        exif = get_exif(path)
        if exif:
            item['created_at'] = exif['DateTimeOriginal']
        # OSX
        item['tags'] = get_osx_tags(path)
        # IPTC
        iptc = get_iptc(path)
        if iptc:
            # TODO: keywords
            if iptc['headline']:
                item['headline'] = iptc['headline']
            if iptc['caption/abstract']:
                item['caption'] = iptc['caption/abstract'].decode('utf-8')
            item['tags'] = (item['tags'] + iptc['keywords'])
        items.append(item)
    print('items: ', items)

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

parse_metadata()
