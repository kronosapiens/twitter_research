'''
Daniel Kronovet
dbk2123@columbia.edu

Code to copy tweet JSON to AWS S3

Configure as a cron job to run nightly:

To run daily at 1am, run `crontab -e` and add the following line:
0 1 * * * python ~/twitter_research/research/copy_to_s3.py 1 -s -c >> ~/twitter_research/cron.log
'''

import argparse
from datetime import datetime, timedelta
import os
import subprocess

import boto3

import config
from utils import logging
from to_csv import to_csv

### Command Line Options
parser = argparse.ArgumentParser(description='Copy daily tweets to AWS S3')
parser.add_argument('offset', type=int, nargs='?', default=1)
parser.add_argument('-s', '--summarize', dest='summarize', action='store_true', default=False)
parser.add_argument('-c', '--csv', dest='csv', action='store_true', default=False)
args = parser.parse_args()

FILE_TEMPLATE = 'tweets.{}.json'
CSV_TEMPLATE = 'tweets.{}.csv'
SUMMARY_TEMPLATE = 'tweets.{}.summary.json'
SUMMARY_CSV_TEMPLATE = 'tweets.{}.summary.csv'

def upload_file(file_name, path, bucket):
    full_path = '{}/{}'.format(path, file_name)
    s3.meta.client.upload_file(
        full_path, bucket, file_name, ExtraArgs={'ACL': 'public-read'})

today = datetime.today()
date_to_copy = (today - timedelta(days=args.offset)).strftime('%m.%d.%Y')

path_root = os.path.dirname(os.path.abspath(__file__))
path = path_root + '/../' + config.DATA_DIR

s3 = boto3.resource('s3')


print '[{}] Beginning run...'.format(today)

file_name = FILE_TEMPLATE.format(date_to_copy)
summary_name = SUMMARY_TEMPLATE.format(date_to_copy)
csv_name = CSV_TEMPLATE.format(date_to_copy)
summary_csv_name = SUMMARY_CSV_TEMPLATE.format(date_to_copy)

if args.summarize:
    print 'Generating summary of', file_name, '...'
    cmd = "awk 'NR == 1 || NR % {freq} == 0' {path}/{source} > {path}/{dest}"
    cmd = cmd.format(freq=config.SUMMARIZE_FREQUENCY, path=path, source=file_name, dest=summary_name)

    try:
        subprocess.call(cmd, shell=True)
        print 'Summary created!'
    except OSError as ex:
        logging.warning(ex)
        print 'Summary creation failed for reason:', ex

    try:
        upload_file(summary_name, path, config.SUMMARY_BUCKET)
        print 'Summary copied!'
    except OSError as ex:
        logging.warning(ex)
        print 'Summary copy failed for reason:', ex

if args.csv:
    print 'Generating CSV of', file_name, '...'
    try:
        to_csv('{}/{}'.format(path, file_name), '{}/{}'.format(path, csv_name), level=3)
        print 'CSV created!'
    except Exception as ex:
        logging.warning(ex)
        print 'CSV creation failed for reason:', ex

    try:
        upload_file(csv_name, path, config.CSV_BUCKET)
        print 'CSV copied!'
    except OSError as ex:
        logging.warning(ex)
        print 'Copy failed for reason:', ex


if args.summarize and args.csv:
    print 'Generating Summary CSV of', file_name, '...'
    try:
        to_csv('{}/{}'.format(path, summary_name), '{}/{}'.format(path, summary_csv_name), level=3)
        print 'Summary CSV created!'
    except Exception as ex:
        logging.warning(ex)
        print 'Summary CSV creation failed for reason:', ex

    try:
        upload_file(summary_csv_name, path, config.SUMMARY_CSV_BUCKET)
        print 'Summary CSV copied!'
    except OSError as ex:
        logging.warning(ex)
        print 'Copy failed for reason:', ex


print 'Copying tweets from {}...'.format(file_name)
try:
    upload_file(file_name, path, config.JSON_BUCKET)
    print 'Tweets copied!'
except OSError as ex:
    logging.warning(ex)
    print 'Copy failed for reason:', ex

# Clean up files
if args.summarize:
    os.remove('{}/{}'.format(path, summary_name))
    print 'Sumary deleted!'

if args.csv:
    os.remove('{}/{}'.format(path, csv_name))
    print 'CSV deleted!'

if args.summarize and args.csv:
    os.remove('{}/{}'.format(path, summary_csv_name))
    print 'Summary CSV deleted!'

os.remove('{}/{}'.format(path, file_name))
print 'File deleted!'



