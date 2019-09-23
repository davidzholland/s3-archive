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
import glob
import rawpy


# base_directory = '/Users/david/Pictures/'
base_directory = '/Volumes/Public/Shared Pictures/'
thumb_directory = '/Users/david/Thumbs/'
sample_paths = []
allowed_directory_patterns = [
    '20180915rockawayhockey'
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
            if 'Orientation' in exif:
                item['orientation'] = exif['Orientation']

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
    if (len(paths) == 0):
        return
    print('paths: ' + str(len(paths)))
    batches = math.ceil(len(paths)/batch_count)
    print('batches: ' + str(batches))
    for i in range(0, batches):
        print(i)
        start = i * batch_count
        end = start + batch_count
        print('start: ', start)
        print('end: ', end)
        print(paths[start:end][0])
        existing_thumbs = 0
        for path in paths[start:end]:
            thumb_path = os.path.join(thumb_directory, path)
            if os.path.exists(thumb_path):
                existing_thumbs += 1
        if existing_thumbs == 0:
            items = parse_metadata(paths[start:end])
            create_thumbs(items)
            # update_database(items)
            time.sleep(.5)
        else:
            print('Already thumbs in this batch: ' + str(existing_thumbs))

def get_file_paths():
    paths = get_directory_files(allowed_directory_patterns[0], allowed_directory_patterns)
    # print('get_file_paths: ', len(paths))
    return paths

def get_directory_files(directory, allowed_patterns = []):
    file_paths = []
    for pattern in allowed_patterns:
        if directory[:len(pattern)] != pattern:
            return file_paths
    for (dirpath, dirnames, filenames) in walk(os.path.join(base_directory, directory), allowed_patterns):
        for filename in filenames:
            if filename[0:1] != '.':
                file_paths.append(os.path.join(directory, filename))
        for dirname in dirnames:
            if dirname[0:1] != '.':
                sub_files = get_directory_files(os.path.join(directory, dirname), allowed_patterns)
                file_paths = (file_paths + sub_files)
        break
    return file_paths

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
        if os.path.isdir(os.path.join(a_dir, name))]

def create_thumbs(items):
    for item in items:
        path = item['file_path']
        img = open_image(path)
        if img is not None:
            thumb_path = os.path.join(thumb_directory, path)
            if thumb_path[-4:].lower() != '.jpg':
                thumb_path = thumb_path + '.jpg'
            create_thumbnail(img, thumb_path, item)

def create_thumbnail(img, thumb_path, item):
    try:
        img.thumbnail((250, 250), Image.ANTIALIAS)
        img = apply_image_orientation(img, item)
        thumb_base_path = os.path.dirname(os.path.abspath(thumb_path))
        if not os.path.exists(thumb_base_path):
            os.makedirs(thumb_base_path)
        img.save(thumb_path, "JPEG")
    except:
        print('Unable to thumbnail: ' + thumb_path)

def open_image(path):
    img = None
    try:
        if (path[-4:].lower() == '.jpg' or path[-5:].lower() == '.jpeg'):
            img = Image.open(os.path.join(base_directory, path))
        elif (path[-4:].lower() == '.nef'):
            raw = rawpy.imread(os.path.join(base_directory, path))
            rgb = raw.postprocess()
            img = Image.fromarray(rgb) # Pillow image
    except:
        print('Unable to open image: ' + path)
    return img

def apply_image_orientation(img, item):
    if 'orientation' in item:
        if item['orientation'] == 3:
            img=img.rotate(180, expand=True)
        elif item['orientation'] == 6:
            img=img.rotate(270, expand=True)
        elif item['orientation'] == 8:
            img=img.rotate(90, expand=True)
    return img

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
                    'Name': 'lc_headline',
                    'Value': item['headline'][:1024].lower(),
                    'Replace': True
                },
                {
                    'Name': 'caption',
                    'Value': item['caption'][:1024],
                    'Replace': True
                },
                {
                    'Name': 'lc_caption',
                    'Value': item['caption'][:1024].lower(),
                    'Replace': True
                },
                {
                    'Name': 'tags',
                    'Value': ','.join(item['tags'][:1024]),
                    'Replace': True
                },
                {
                    'Name': 'lc_tags',
                    'Value': ','.join(item['tags'][:1024].lower()),
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

def get_to_be_thumbed_directories():
    base_directories = get_immediate_subdirectories(base_directory)
    thumb_directories = get_immediate_subdirectories(thumb_directory)
    unthumbed_directories = list(set(base_directories) - set(thumb_directories))
    unthumbed_directories = [ x for x in unthumbed_directories if x[:4].isdigit() ]
    # print(unthumbed_directories)
    # print(str(len(base_directories) - len(unthumbed_directories)) + ' of ' + str(len(base_directories)))
    print('Unthumbed: ', len(unthumbed_directories))
    return unthumbed_directories

def get_remaining_to_lowercase():
    client = boto3.client('sdb')
    response = client.select(
        SelectExpression='SELECT COUNT(*) FROM `photo-archive` WHERE `lc_file_path` IS NULL'
    )
    attributes = parseSDBItemAttributes(response['Items'][0])
    print('Remaining: ', attributes['Count'])
    return int(attributes['Count'])

def copy_to_lowercase_columns():
    print('Copying columns to lowercase...')
    client = boto3.client('sdb')
    response = client.select(
        SelectExpression='SELECT * FROM `photo-archive` WHERE `lc_file_path` IS NULL LIMIT 25'
    )
    simpledb_items = []
    for item in response['Items']:
        item_attributes = parseSDBItemAttributes(item)
        new_attributes = []
        new_attributes.append({
            'Name': 'lc_file_path',
            'Value': item['Name'].lower(),
            'Replace': True
        })
        if 'headline' in item_attributes:
            new_attributes.append({
                'Name': 'lc_headline',
                'Value': item_attributes['headline'].lower(),
                'Replace': True
            })
        if 'caption' in item_attributes:
            new_attributes.append({
                'Name': 'lc_caption',
                'Value': item_attributes['caption'].lower(),
                'Replace': True
            })
        if 'tags' in item_attributes:
            new_attributes.append({
                'Name': 'lc_tags',
                'Value': item_attributes['tags'].lower(),
                'Replace': True
            })
        if len(new_attributes) > 0:
            simpledb_items.append({
                'Name': item['Name'],
                'Attributes': new_attributes
            })
    print('simpledb_items: ', len(simpledb_items))
    if len(simpledb_items) > 0:
        response = client.batch_put_attributes(
            DomainName='photo-archive',
            Items=simpledb_items
        )

def parseSDBItemAttributes(item):
    attributes = {}
    for attribute in item['Attributes']:
        key = attribute['Name']
        attributes[key] = attribute['Value']
    return attributes

# unthumbed_directories = get_to_be_thumbed_directories()
# allowed_directory_patterns = sorted(unthumbed_directories, reverse=True)
# to_finish_thumbnailing = [
#     '20180624iphone',
#     '20180209iphone2',
#     '20151002nyc',
#     '20151006honeymoon',
#     '20151120passport',
#     '20151225five-weddings',
#     '20090413easter'
# ]
# allowed_directory_patterns = to_finish_thumbnailing
# print(allowed_directory_patterns)
# while len(allowed_directory_patterns) > 0:
#     allowed_directory_patterns = [ allowed_directory_patterns.pop(0) ]
#     print('allowed_directory_patterns', allowed_directory_patterns)
#     handle()

# TODO: Identify recently updated directories/files for re-indexing
# TODO: Lowercase all search values in database and lowercase all provided search terms

# remaining_count = get_remaining_to_lowercase()
# while remaining_count > 0:
#     copy_to_lowercase_columns()
#     remaining_count = remaining_count - 25
#     print('remaining_count: ', remaining_count)
