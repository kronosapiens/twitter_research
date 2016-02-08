'''
Daniel Kronovet
dbk2123@columbia.edu

Code to copy tweet JSON to AWS S3

Configure as a cron job to run nightly:

To run daily at 1am, run `crontab -e` and add the following line:
0 1 * * * python ~/twitter_research/research/copy_to_s3.py 1 -s >> ~/twitter_research/cron.log
'''

import argparse
from datetime import datetime, timedelta
import os
import subprocess

import boto3

import config
from utils import logging

### Command Line Options
parser = argparse.ArgumentParser(description='Copy daily tweets to AWS S3')
parser.add_argument('offset', type=int, nargs='?', default=1)
parser.add_argument('-s', '--summarize', dest='summarize', action='store_true', default=False)
args = parser.parse_args()

FILE_TEMPLATE = 'tweets.{}.json'
SUMMARY_TEMPLATE = 'tweets.{}.summary.json'

def upload_file(file_name, path):
    full_path = '{}/{}'.format(path, file_name)
    s3.meta.client.upload_file(
        full_path, config.S3_BUCKET, file_name, ExtraArgs={'ACL': 'public-read'})

today = datetime.today()
date_to_copy = (today - timedelta(days=args.offset)).strftime('%m.%d.%Y')

s3 = boto3.resource('s3')

file_name = FILE_TEMPLATE.format(date_to_copy)
path_root = os.path.dirname(os.path.abspath(__file__))
path = path_root + '/../' + config.DATA_DIR

print '[{}] Copying tweets from {}...'.format(today, file_name)
try:
    upload_file(file_name, path)
    print 'Tweets copied!'
except OSError as ex:
    logging.warning(ex)
    print 'Copy failed for reason:', ex

if args.summarize:
    print 'Generating summary of', file_name, '...'
    summary_name = SUMMARY_TEMPLATE.format(date_to_copy)
    cmd = "awk 'NR == 1 || NR % {freq} == 0' {path}/{source} > {path}/{dest}"
    cmd = cmd.format(freq=config.SUMMARIZE_FREQUENCY, path=path, source=file_name, dest=summary_name)

    try:
        subprocess.call(cmd, shell=True)
        print 'Summary created!'
    except OSError as ex:
        logging.warning(ex)
        print 'Summary creation failed for reason:', ex

    try:
        upload_file(summary_name, path)
        print 'Summary copied!'
    except OSError as ex:
        logging.warning(ex)
        print 'Summary copy failed for reason:', ex




