#! /usr/bin/env python
'''
# Author: Achim Dreyer <1019082+jd666@users.noreply.github.com>
# merge slack channel export files into a channel log
'''

from __future__ import print_function
import argparse
import sys
import json
import codecs
from os import listdir
from os.path import join
from datetime import datetime
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

def get_filelist(mypath=None):
    ''' build a file listing hash for directory <mypath> '''
    filehash = dict({})
    for filename in listdir(mypath):
        filehash[filename] = join(mypath, filename)
    return filehash

def ts_2_utc(posix_time=None):
    ''' convert a posix timestamp to a UTC time string '''
    if posix_time:
        # return datetime.utcfromtimestamp(posix_time).strftime('%Y-%m-%dT%H:%M:%SZ')
        return datetime.utcfromtimestamp(posix_time).strftime('%Y-%m-%d %H:%M:%S (UTC)')
    return None

def json_read(filename=None):
    ''' Read JSON encoded data from file '''
    if not filename:
        return False
    try:
        if not filename.endswith('.json'):
            filename += '.json'
        with open(filename, "r") as filehandler:
            data = json.load(filehandler)
        filehandler.close()
    except IOError as excpt:
        print("ERROR: %s" % excpt)
        return False
    except (ValueError, KeyError, TypeError) as excpt:
        print("JSON format error in %s" % filename)
        print("ERROR: %s" % excpt)
        return False
    return data

def write_file(mypath=None, data=None):
    ''' write data to file '''
    if not data:
        return True
    try:
        if mypath:
            outfile = open(mypath, 'w')
        else:
            outfile = sys.stdout
        if isinstance(data, list):
            for line in data:
                print(line, file=outfile)
        else:
            print(data, file=outfile)
        outfile.close()
    except IOError as excpt:
        print("ERROR: %s" % excpt)
        return False
    except Exception as excpt:
        print("ERROR: Couldn't write file %s\n%s\n" % (mypath, excpt))
        return False
    return True


def main():
    ''' main routine '''
    parser = argparse.ArgumentParser(description="Create a readable Slack channel log file")
    parser.add_argument("-d", "--data", action="store", required=True,
                        help="data directory")
    args = parser.parse_args()
    output = list()

    if not args.data:
        print("ERROR: data dir missing")
        return 1
    print("data source: %s" % args.data)
    files = get_filelist(args.data)
    if 'users.json' not in files:
        print("ERROR: users file missing")
        return 2
    userdata = json_read(files.pop('users.json', None))
    users = dict({})
    for entry in userdata:
        if 'name' in entry:
            users[entry['id']] = entry['name']
        elif 'real_name' in entry:
            users[entry['id']] = entry['real_name']
        else:
            users[entry['id']] = entry['id']
    if not users:
        print("ERROR: wrong file format")
        return 3

    try:
        for logslice in sorted(files.keys()):
            slicedata = json_read(files[logslice])
            for entry in slicedata:
                timestamp = ts_2_utc(float(entry['ts']))
                sender = users[entry['user']]
                text = entry['text'].encode('ascii', 'ignore').rstrip()
                if text.count('<!'):
                    textn = text.replace('<!here>', '@here')
                    text = textn
                if text.count('<@'):
                    for user in users.keys():
                        textn = text.replace('<@%s>' % user, '@%s' % users[user])
                        text = textn
                output.append("%s %-20s %s" % (timestamp, sender+':', text))
    except KeyboardInterrupt:
        print("aborted")
        return 4
    print('Writing to %s.txt' % args.data)
    write_file(args.data+'.txt', output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
