#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.1'

import argparse
import os
import subprocess
import ConfigParser
import sys
import shutil

# main
def parse_args():
    parser = argparse.ArgumentParser(description='Build rpm inside docker image')
    parser.add_argument('-c', '--config', default='docker-rpmbuilder.ini',
        help='Config file [default: docker-rpmbuilder.ini]')
    parser.add_argument('-d', '--debug', action='store_true',
        help='Print more debug messages')
    parser.add_argument('-s', '--section', default='main',
        help='Switch between config sections [default: main]')

    subparsers = parser.add_subparsers()

    # build docker image
    parser_image = subparsers.add_parser('image', help='Build docker image')
    parser_image.set_defaults(func=image)

    # build rpm package inside docker image
    parser_package = subparsers.add_parser('package',
        help='Build rpm package inside docker container')
    parser_package.add_argument('-r', '--remove', action='store_true',
        help='Clear temporary files before building package')
    parser_package.set_defaults(func=package)

    # shell
    parser_shell = subparsers.add_parser('shell',
        help='Run interactive shell inside docker container')
    parser_shell.set_defaults(func=shell)

    # generate
    parser_generate = subparsers.add_parser('generate',
        help='Generate and write Dockerfile to disk')
    parser_generate.set_defaults(func=generate_dockerfile)

    # clear
    parser_clear = subparsers.add_parser('clear', help='Clear temporary files')
    parser_clear.set_defaults(func=clear)

    # show
    parser_show = subparsers.add_parser('show', help='Show config file and exit')
    parser_show.set_defaults(func=show)

    return parser.parse_args()


## helper functions
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
    print '===> Generate Dockerfile from "{0}"'.format(template)
    if not os.path.exists(template):
        print 'ERR> "{0}" does not exist'.format(template)
        sys.exit(1)
    userinfo = get_userinfo()
    content = ''
    with open(template, 'r') as f:
        content = f.read()

    print '     USERID -> {USERID}, GROUPID -> {GROUPID}'.format(**userinfo)
    _content = content.format(**userinfo)

    print _content

    """Write Dockerfile to disk"""
    print '===> Write Dockerfile do disk'
    with open('Dockerfile', 'w') as f:
        f.write(_content)

    return True

def generate_buildnumber():
    """Get build number from BUILD_NUMBER variable"""
    try:
        build_number = os.environ['BUILD_NUMBER']
    except KeyError:
        build_number = '0'
    return build_number

def generate_commit():
    """Generate short commit version"""
    commit = subprocess.check_output('git rev-parse HEAD', shell=True)[0:7]
    return commit

def generate_release(git):
    """Generate release metatag from current git commit"""
    buildnumber = generate_buildnumber()
    if git:
        commit = generate_commit()
        return '{buildnumber}.git{commit}'.format(**locals())
    else:
        return buildnumber

def generate_rpmbuild():
    """Generate minimal rpmbuild directory tree"""
    tree = ['rpmbuild/', 'rpmbuild/SOURCES/', 'rpmbuild/SPECS/']
    print '===> Create rpmbuild directory tree: {0}'.format(', '.join(tree))
    for directory in tree:
        if not os.path.exists(directory):
            os.mkdir(directory)
            
def create_tmpdir():
    """Create temporary working directory from rpmbuild"""
    if not os.path.exists('tmp'):
        shutil.copytree('rpmbuild', 'tmp')

def change_directory(workdir):
    """Change directory to workdir"""
    if not os.path.exists(workdir):
        print 'ERR> "{0}" does not exist'.format(workdir)
        sys.exit(3)
    print '===> Change current directory to "{0}"'.format(workdir)
    os.chdir(workdir)

def load_config(filename, section):
    """Verify and print config.ini"""
    if not os.path.exists(filename):
        print 'ERR> "{0}" does not exist'.format(filename)
        sys.exit(3)

    default_config = {
        'imagename': 'builder-example',
        'dockerfile' : 'Dockerfile.template',
        'spec': 'default.spec',
        'prepare_cmd': None,
        'download': False,
        'git': False,
        'workdir': 'packaging',
    }
    config_file = ConfigParser.SafeConfigParser(default_config)
    config_file.read(filename)

    config = {}
    try:
        config['imagename'] = config_file.get(section, 'imagename')
        config['dockerfile'] = config_file.get(section, 'dockerfile')
        config['spec'] = config_file.get(section, 'spec')
        config['prepare_cmd'] = config_file.get(section, 'prepare_cmd')
        config['download'] = config_file.getboolean(section, 'download')
        config['git'] = config_file.getboolean(section, 'git')
        config['workdir'] = config_file.get(section, 'workdir')
    except ConfigParser.NoSectionError:
        print 'ERR> Failed to parse config from "{0}": section "{1}" not found'.format(filename, section)
        sys.exit(3)

    return config


## parser main functions
def clear(args, config):
    """Remove temporary files"""
    tmps = ['Dockerfile', 'tmp/']
    print '===> Remove temporary file/directory: {}'.format(', '.join(tmps))
    for tmp in tmps:
        if os.path.exists(tmp):
            if os.path.isfile(tmp): os.remove(tmp)
            if os.path.isdir(tmp): shutil.rmtree(tmp)

def shell(args, config):
    """Run docker interactive shell"""
    print '===> Run docker interactive shell from image: {0}'.format(config['imagename'])
    create_tmpdir()
    rc = subprocess.call('docker run --rm -it \
        -v $(pwd)/tmp/:/home/builder/rpmbuild {0} /bin/bash'.format(config['imagename']),
        shell=True)
    if rc != 0: exit(rc)

def package(args, config):
    """Build rpm package inside docker container"""
    release = generate_release(config['git'])
    print '===> Build rpm package, release: {0}'.format(release)

    # prepare actions
    if args.remove:
        clear(args, config)

    create_tmpdir()
    if config['prepare_cmd']:
        print '===> Run prepare command: {0}'.format(config['prepare_cmd'])
        rc = subprocess.call(config['prepare_cmd'], shell=True)
        if rc != 0: exit(rc)

    download_cmd = ''
    if config['download']:
        download_cmd = 'spectool -g -R SPECS/{0};'.format(config['spec'])
    shell_cmd = '{0} rpmbuild --define \'release {1}\' -ba \
        --buildroot=/tmp/build SPECS/{2}'.format(download_cmd, release, config['spec'])
    docker_cmd = 'docker run --rm -v $(pwd)/tmp/:/home/builder/rpmbuild \
        -t {0} /bin/bash -c "{1}"'.format(config['imagename'], shell_cmd)

    print '===> Run compilation command: {0}'.format(docker_cmd)
    rc = subprocess.call(docker_cmd, shell=True)
    if rc != 0: exit(rc)

def image(args, config):
    """Build docker image"""
    buildnumber = generate_buildnumber()
    generate_dockerfile(config['dockerfile'])
    print '===> Build docker image {0}:{1}'.format(config['imagename'], buildnumber)
    rc = subprocess.call('docker build -t {0} .'.format(config['imagename']), shell=True)
    if rc != 0: exit(rc)
    if buildnumber != '0':
        subprocess.call('docker tag {0}:latest {0}:{1}'.format(config['imagename'], buildnumber),
            shell=True)

def show(args, config):
    print '===> Load {0}'.format(args.config)
    for k, v in config.items():
        print '     {0:12} -> {1}'.format(k, v)


### main
def main():
    """Main function"""
    # parse argumets, load config
    args = parse_args()
    config = load_config(args.config, args.section)
    
    # debug mode
    if args.debug:
        print '-----'
        print 'args: {0}'.format(args)
        print 'config: {0}'.format(config)
        print 'function name: {0}'.format(args.func.__name__)
        print '-----'

    # ignore change directory for some functions
    if args.func.__name__ not in ('show'):
        change_directory(config['workdir'])

    args.func(args, config)

if __name__ == '__main__':
    main()
