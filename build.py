#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import argparse
import subprocess
import sys

DOCKERFILE = 'sources/Dockerfile.template'

def parse_args():
    parser = argparse.ArgumentParser(description='Build rpm inside docker image')
    subparsers = parser.add_subparsers()
    # clear
    parser_clear = subparsers.add_parser('clear', help='Remove temporary files')
    parser_clear.set_defaults(func=clear)
    # generate
    parser_generate = subparsers.add_parser('generate', help='Generate and write Dockerfile to disk')
    parser_generate.add_argument("-t", "--template", required=False, type=str, default=DOCKERFILE)
    parser_generate.set_defaults(func=generate_write_dockerfile)
    # shell
    # build docker image
    # run inside docker image
    return parser.parse_args()

def get_userinfo():
    """Get current user UID and GID"""
    uid = os.getuid()
    gid = os.getgid()
    return {'USERID': uid, 'GROUPID': gid}

def generate_dockerfile(template):
    """Generate Dockerfile from template"""
    print '===> Generate Dockerfile from {0}'.format(template)
    userinfo = get_userinfo()
    content = ''
    with open(DOCKERFILE, 'r') as f:
        content = f.read()

    print '===> Replacement content: USERID={USERID}, GROUPID={GROUPID}'.format(**userinfo)
    _content = content.format(**userinfo)
    return _content

def write_dockerfile(content):
    """Write Dockerfile to disk"""
    print '===> Write Dockerfile do disk'
    with open('Dockerfile', 'w') as f:
        f.write(content)
    return True

def generate_write_dockerfile(args):
    if not os.path.exists(args.template):
        print 'ERR> {0} does not exist'.format(args.template)
        sys.exit(1)
    content = generate_dockerfile(args.template)
    print content
    write_dockerfile(content)

def clear(args):
    """Remove temporary files"""
    tmps = ['Dockerfile', 'rpmbuild']
    print '===> Remove temporary file/directory: {}'.format(', '.join(tmps))
    for tmp in tmps:
        if os.path.exists(tmp):
            if os.path.isfile(tmp): os.remove(tmp)
            if os.path.isdir(tmp): shutil.rmtree(tmp)
    return True

def main():
    content = generate_dockerfile()
    print content
    write_dockerfile(content)
    clear()

if __name__ == '__main__':
    args = parse_args()
    args.func(args)
