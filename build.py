#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import subprocess
import sys
import ConfigParser


# main
def parse_args():
    parser = argparse.ArgumentParser(description='Build rpm inside docker image')
    subparsers = parser.add_subparsers()

    # build docker image
    parser_image = subparsers.add_parser('image', help='Build docker image')
    parser_image.add_argument('-t', '--template', required=False, type=str, 
        help='Path to Dockerfile.template', 
        default=config['dockerfile'])
    parser_image.set_defaults(func=image)

    # build rpm package inside docker image
    parser_package = subparsers.add_parser('package',
        help='Build rpm package inside docker container')
    parser_package.add_argument('-g', '--git', action='store_true',
        help='Append current git commit to RELEASE')
    parser_package.add_argument('-n', '--nodownload', action='store_true',
        help='Do not download source with spectool (need source archive inside SOURCES)')
    parser_package.set_defaults(func=package)

    # shell
    parser_shell = subparsers.add_parser('shell',
        help='Run docker interactive shell')
    parser_shell.set_defaults(func=shell)

    # generate
    parser_generate = subparsers.add_parser('generate',
        help='Generate and write Dockerfile to disk')
    parser_generate.add_argument('-t', '--template',
        help='Path to Dockerfile.template', required=False, type=str,
        default=config['dockerfile'])
    parser_generate.set_defaults(func=generate_write_dockerfile)

    # clear
    parser_clear = subparsers.add_parser('clear', help='Remove temporary files')
    parser_clear.add_argument('-f', '--full', action='store_true',
        help='Remove temporary files inside rpmbuild')
    parser_clear.set_defaults(func=clear)

    return parser.parse_args()


# helper functions
def get_userinfo():
    """Get current user UID and GID"""
    uid = os.getuid()
    gid = os.getgid()
    return {
        'USERID': uid,
        'GROUPID': gid,
    }

def generate_dockerfile(template):
    """Generate Dockerfile from template"""
    print '===> Generate Dockerfile from {0}'.format(template)
    if not os.path.exists(template):
        print 'ERR> {0} does not exist'.format(template)
        sys.exit(1)
    userinfo = get_userinfo()
    content = ''
    with open(template, 'r') as f:
        content = f.read()

    print '===> Replacement content: USERID -> {USERID}, GROUPID -> {GROUPID}'.format(**userinfo)
    _content = content.format(**userinfo)
    return _content

def write_dockerfile(content):
    """Write Dockerfile to disk"""
    print '===> Write Dockerfile do disk'
    with open('Dockerfile', 'w') as f:
        f.write(content)
    return True

def generate_imagename(spec):
    """Generate docker image name from spec path"""
    _image = spec.split('/')[-1].split('.')[0]
    image = '{0}{1}'.format(config['image_prefix'], _image)
    print '===> Generate docker image name from spec: {spec} -> {image}'.format(**locals())
    return image

def generate_buildnumber():
    """Get build number from BUILD_NUMBER variable"""
    try:
        build_number = os.environ['BUILD_NUMBER']
    except KeyError:
        build_number = '0'
    return build_number

def generate_commit():
    """Generate release metatag from current git commit"""
    commit = subprocess.check_output('git rev-parse HEAD', shell=True)[0:7]
    return commit

def generate_release(git):
    buildnumber = generate_buildnumber()
    if git:
        commit = generate_commit()
        return '{buildnumber}.git{commit}'.format(**locals())
    else:
        return buildnumber

def generate_rpmbuild_tree():
    tree = ['rpmbuild/', 'rpmbuild/SOURCES/', 'rpmbuild/SPECS/']
    print '===> Create rpmbuild directory tree: {0}'.format(', '.join(tree))
    for directory in tree:
        if not os.path.exists(directory):
            os.mkdir(directory)

def verify_config():
    """Verify and print config.py"""
    default_config = {
        'image_prefix': 'builder-',
        'dockerfile' : 'Dockerfile.template',
        'spec': 'rpmbuild/SPECS/default.spec',
        'prepare_cmd': None,
    }
    config_file = ConfigParser.SafeConfigParser(default_config)
    config_file.read('config.ini')
    section = 'main'

    config = {}
    config['image_prefix'] = config_file.get(section, 'image_prefix')
    config['dockerfile'] = config_file.get(section, 'dockerfile')
    config['spec'] = config_file.get(section, 'spec')
    config['prepare_cmd'] = config_file.get(section, 'prepare_cmd')

    print '===> Read and parse config from config.py'
    for k, v in config.items():
        print '     {0:12} -> {1}'.format(k, v)

    return config


# parser main functions
def generate_write_dockerfile(args):
    """Generate, print and write to disk Dockerfile"""
    content = generate_dockerfile(args.template)
    print content
    write_dockerfile(content)

def clear(args):
    """Remove temporary files"""
    tmps = ['Dockerfile', 'rpmbuild/BUILD', 'rpmbuild/BUILDROOT']
    if args.full:
        tmps.append('rpmbuild/RPMS')
        tmps.append('rpmbuild/SRPMS')
    print '===> Remove temporary file/directory: {}'.format(', '.join(tmps))
    for tmp in tmps:
        if os.path.exists(tmp):
            if os.path.isfile(tmp): os.remove(tmp)
            if os.path.isdir(tmp): shutil.rmtree(tmp)

def shell(args):
    """Run docker interactive shell"""
    image = generate_imagename(config['spec'])
    print '===> Run docker interactive shell from image: {0}'.format(image)
    rc = subprocess.call('docker run --rm -it \
        -v $(pwd)/rpmbuild/:/home/builder/rpmbuild {0} /bin/bash'.format(image),
        shell=True)
    if rc != 0: exit(4)

def package(args):
    """Build rpm package inside docker container"""
    SPEC = config['spec']
    PREPARE_CMD = config['prepare_cmd']
    release = generate_release(args.git)
    image = generate_imagename(SPEC)
    generate_rpmbuild_tree()
    print '===> Build rpm package, release: {0}'.format(release)
    download_cmd = ''
    if not args.nodownload:
        download_cmd = 'spectool -g -R {0};'.format(SPEC)
    if PREPARE_CMD:
        print '===> Run prepare command: {0}'.format(PREPARE_CMD)
        rc = subprocess.call(PREPARE_CMD, shell=True)
        if rc != 0: exit(3)
    shell_cmd = '{0} rpmbuild --define \'release {1}\' -ba \
        --buildroot=/tmp/build {2}'.format(download_cmd, release, SPEC)
    docker_cmd = 'docker run --rm -v $(pwd)/rpmbuild/:/home/builder/rpmbuild \
        -t {image} /bin/bash -c "{shell_cmd}"'.format(**locals())
    print '===> Run compilation command: {0}'.format(docker_cmd)
    rc = subprocess.call(docker_cmd, shell=True)
    if rc != 0: exit(2)

def image(args):
    """Build docker image"""
    image = generate_imagename(config['spec'])
    buildnumber = generate_buildnumber()
    generate_write_dockerfile(args)
    print '===> Build docker image {image}:{buildnumber}'.format(**locals())
    subprocess.call('docker build -t {image} .'.format(**locals()), shell=True)
    if buildnumber != '0':
        subprocess.call('docker tag {image}:latest {image}:{buildnumber}'.format(**locals()),
            shell=True)

if __name__ == '__main__':
    config = verify_config()
    args = parse_args()
    args.func(args)
