import json
import boto3
import os
from iptcinfo3 import IPTCInfo
from PIL import Image
from PIL.ExifTags import TAGS
import mac_tag
from libxmp.utils import file_to_dict
from libxmp import XMPFiles, consts
from os import walk
import chardet
import math
import time
import platform
from datetime import datetime


base_directory = ''
sample_paths = []

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

def parse_metadata(paths):
    items = []
    for path in paths:
        full_path = os.path.join(base_directory, path)
        item = {
            'file_path': path,
            'created_at': '',
            'headline': '',
            'caption': '',
            'tags': [],
            'latitude': '',
            'longitude': ''
        } 
        # XMP
        xmp = get_xmp(full_path)
        if xmp:
            if 'description' in xmp:
                item['caption'] = xmp['description']
        # EXIF
        exif = get_exif(full_path)
        if exif != False:
            try:
                if 'DateTimeOriginal' in exif:
                    item['created_at'] = str(datetime.strptime(exif['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S'))
                elif 'DateTime' in exif:
                    item['created_at'] = str(datetime.strptime(exif['DateTime'], '%Y:%m:%d %H:%M:%S'))
            except Exception as e:
                print(e)
            if item['created_at'] == '':
                file_creation_timestamp = get_file_creation_date(full_path)
                item['created_at'] = str(datetime.fromtimestamp(file_creation_timestamp))

        # OSX
        item['tags'] = get_osx_tags(full_path)
        # IPTC
        iptc = get_iptc(full_path)
        # print('full_path: ', full_path)
        # print('iptc: ', iptc)
        if iptc:
            if iptc['headline']:
                item['headline'] = decode_bytes(iptc['headline'])
            if iptc['caption/abstract']:
                item['caption'] = decode_bytes(iptc['caption/abstract'])
            for keyword in iptc['keywords']:
                item['tags'].append(decode_bytes(keyword))
        items.append(item)
    return items

def decode_bytes(bytes_object):
    try:
        return bytes_object.decode("utf-8")
    except:
        return auto_decode(bytes_object)

def auto_decode(bytes_object):
    try:
        the_encoding = chardet.detect(bytes_object)['encoding']
        if the_encoding is None:
            return ""
        return bytes_object.decode(the_encoding)
    except Exception as e:
        print(e)
        return str(bytes_object)

def handle():
    batch_count = 25
    paths = get_file_paths()
    print('paths: ' + str(len(paths)))
    batches = math.ceil(len(paths)/batch_count)
    print('batches: ' + str(batches))
    for i in range(0, batches):
        print(i)
        start = i * batch_count
        end = start + batch_count
        print('start: ', start)
        print('end: ', end)
        # print(paths[start:end])
        items = parse_metadata(paths[start:end])
        update_database(items)
        time.sleep(.5)

def get_file_paths():
    paths = sample_paths
    directories = get_immediate_subdirectories(base_directory)
    for directory in directories:
        paths = paths + get_directory_files(directory)
    return paths

def get_directory_files(directory):
    file_paths = []
    # if directory[:2] == '20' and directory[:4] <= '2017':
    print('directory:', directory)
    for (dirpath, dirnames, filenames) in walk(os.path.join(base_directory, directory)):
        for filename in filenames:
            file_paths.append(os.path.join(directory, filename))
        for dirname in dirnames:
            sub_files = get_directory_files(os.path.join(directory, dirname))
            file_paths = (file_paths + sub_files)
        break
    return file_paths

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
        if os.path.isdir(os.path.join(a_dir, name))]

def update_database(items):
    print('Updating database...')
    client = boto3.client('sdb')
    simpledb_items = []
    for item in items:
        simpledb_items.append({
            'Name': item['file_path'],
            'Attributes': [
                {
                    'Name': 'headline',
                    'Value': item['headline'][:1024],
                    'Replace': True
                },
                {
                    'Name': 'caption',
                    'Value': item['caption'][:1024],
                    'Replace': True
                },
                {
                    'Name': 'tags',
                    'Value': ','.join(item['tags'][:1024]),
                    'Replace': True
                },
                {
                    'Name': 'created_at',
                    'Value': item['created_at'],
                    'Replace': True
                },
                {
                    'Name': 'last_indexed_at',
                    'Value': str(datetime.now()),
                    'Replace': True
                }
            ]
        })
    response = client.batch_put_attributes(
        DomainName='photo-archive',
        Items=simpledb_items
    )
    print('response: ', response)

def get_file_creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

handle()
