#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import argparse
import os
import shutil
import subprocess
import sys

__version__ = '0.4pre'

# main
def parse_args():
    parser = argparse.ArgumentParser(description='Build package inside docker container')
    parser.add_argument('-c', '--config', default='docker-builder.ini',
        help='Config file [default: docker-builder.ini]')
    parser.add_argument('-d', '--debug', action='store_true',
        help='Print more debug messages')
    parser.add_argument('-s', '--section', default='default',
        help='Switch between config sections [default: default]')

    subparsers = parser.add_subparsers()

    # build docker image
    parser_image = subparsers.add_parser('image', help='Build docker image')
    parser_image.set_defaults(func=image)

    # build rpm package inside docker image
    parser_package = subparsers.add_parser('package',
        help='Build package inside docker container')
    parser_package.add_argument('-r', '--remove', action='store_true',
        help='Clear temporary files before building package')
    parser_package.set_defaults(func=package)

    # shell
    parser_shell = subparsers.add_parser('shell',
        help='Run interactive shell inside docker container')
    parser_shell.set_defaults(func=shell)

    # generate
    parser_generate = subparsers.add_parser('generate',
        help='Generate and write Dockerfile files to disk')
    parser_generate.set_defaults(func=generate)

    # clear
    parser_clear = subparsers.add_parser('clear',
            help='Clear temporary files')
    parser_clear.set_defaults(func=clear)

    # show
    parser_show = subparsers.add_parser('show',
        help='Show configuration and exit')
    parser_show.set_defaults(func=show)

    return parser.parse_args()


## helper functions
def get_userid():
    """Get current user id"""
    return os.getuid()

def get_usergid():
    """Get current group id"""
    return os.getgid()

def generate_dockerfile(template, spec):
    """Generate Dockerfile from template"""
    userid = get_userid()
    groupid = get_usergid()
    print '===> Generate Dockerfile from "{template}"'.format(**locals())
    if not os.path.exists(template):
        print 'Error: "{template}" does not exist'.format(**locals())
        sys.exit(1)
    content = ''
    with open(template, 'r') as f:
        content = f.read()

    print '     userid -> {userid}, groupid -> {groupid}, spec -> {spec}'.format(**locals())
    _content = content.format(**locals())
    print _content

    print '===> Write Dockerfile do disk'
    with open('Dockerfile', 'w') as f:
        f.write(_content)

    return True

def generate_buildnumber():
    """Get build number from BUILD_NUMBER variable"""
    try:
        return os.environ['BUILD_NUMBER']
    except KeyError:
        return '0'

def generate_commit():
    """Generate short commit version"""
    try:
        commit = subprocess.check_output('git rev-parse HEAD', shell=True)[0:7]
    except:
        print 'Error: unable to get git commit version'
        sys.exit(3)
    return commit

def generate_release(git):
    """Generate release metatag from current git commit"""
    buildnumber = generate_buildnumber()
    if git:
        commit = generate_commit()
        return '{buildnumber}.git{commit}'.format(**locals())
    else:
        return buildnumber

def create_tmpdir():
    """Create temporary working directory from build"""
    print '===> Create temporary directory tree inside "build-env"'
    if not os.path.exists('build-env'):
        if os.path.exists('rpmbuild'): shutil.copytree('rpmbuild', 'build-env')
        if os.path.exists('debbuild'): shutil.copytree('debbuild', 'build-env')

def change_directory(workdir):
    """Change directory to workdir"""
    if not os.path.exists(workdir):
        print 'Error: "{0}" does not exist'.format(workdir)
        sys.exit(3)
    print '===> Change current directory to "{0}"'.format(workdir)
    os.chdir(workdir)

def load_config(filename, section):
    """Load and verify docker-builder.ini"""
    if not os.path.exists(filename):
        print 'Error: "{0}" does not exist'.format(filename)
        sys.exit(3)

    default_config = {
        'git': False,
        'image': 'builder',
        'prepare': None,
        'spec': None,
        'workdir': None,
        'dockerfile': 'Dockerfile.template',
        'entrypoint': 'entrypoint.sh',
    }
    config_file = ConfigParser.SafeConfigParser(default_config)
    config_file.read(filename)
    print '===> Available sections: {}'.format(', '.join(config_file.sections()))

    config = {}
    if config_file.has_section(section):
        # get string options
        config['image'] = config_file.get(section, 'image')
        config['prepare'] = config_file.get(section, 'prepare')
        config['spec'] = config_file.get(section, 'spec')
        config['workdir'] = config_file.get(section, 'workdir')
        config['dockerfile'] = config_file.get(section, 'dockerfile')
        config['entrypoint'] = config_file.get(section, 'entrypoint')
        # get boolean option
        try:
            config['git'] = config_file.getboolean(section, 'git')
        except ValueError:
            config['git'] = default_config['git']
    else:
        print 'Error: Failed to parse config from "{0}": section "{1}" not found'.format(filename, section)
        sys.exit(3)

    return config


## parser main functions
def clear(args, config):
    """Remove temporary files"""
    tmps = ['Dockerfile', 'build-env/']
    print '===> Remove temporary file/directory: {}'.format(', '.join(tmps))
    for tmp in tmps:
        if os.path.exists(tmp):
            if os.path.isfile(tmp): os.remove(tmp)
            if os.path.isdir(tmp): shutil.rmtree(tmp)

def shell(args, config):
    """Run docker interactive shell"""
    print '===> Run docker interactive shell from image: {0}'.format(config['image'])
    release = generate_release(config['git'])
    create_tmpdir()

    options = {
        'release': release,
        'spec': config['spec'],
        'image': config['image'],
    }
    docker_cmd = 'docker run --rm -it -v $(pwd)/build-env/:/home/builder/build \
        --entrypoint=/bin/bash \
        -e RELEASE={release} -e SPEC={spec} -t {image}'.format(**options)

    print '===> Run container: {0}'.format(' '.join(docker_cmd.split()))
    rc = subprocess.call(docker_cmd, shell=True)
    if rc != 0: exit(rc)

def package(args, config):
    """Build package inside docker container"""
    release = generate_release(config['git'])
    print '===> Build  package, release: {0}'.format(release)

    # prepare actions
    if args.remove:
        clear(args, config)

    create_tmpdir()
    if config['prepare']:
        print '===> Run prepare script: {0}'.format(config['prepare'])
        rc = subprocess.call(config['prepare'], shell=True)
        if rc != 0: exit(rc)

    options = {
        'release': release,
        'spec': config['spec'],
        'image': config['image'],
    }
    docker_cmd = 'docker run --rm -v $(pwd)/build-env/:/home/builder/build \
        -e RELEASE={release} -e SPEC={spec} -t {image}'.format(**options)

    print '===> Run container: {0}'.format(' '.join(docker_cmd.split()))
    rc = subprocess.call(docker_cmd, shell=True)
    if rc != 0: exit(rc)

def image(args, config):
    """Build docker image"""
    buildnumber = generate_buildnumber()
    generate(args, config)
    print '===> Build docker image {0}:{1}'.format(config['image'], buildnumber)
    rc = subprocess.call('docker build -t {0} .'.format(config['image']), shell=True)
    if rc != 0: exit(rc)
    if buildnumber != '0':
        subprocess.call('docker tag {0}:latest {0}:{1}'.format(config['image'], buildnumber),
            shell=True)

def show(args, config):
    print '===> Load {0}'.format(args.config)
    for k, v in config.items():
        print '     {0:12} -> {1}'.format(k, v)

def generate(args, config):
    generate_dockerfile(config['dockerfile'], config['spec'])


### main
def main():
    """Main function"""
    # reopen stdout file descriptor with write mode
    # and 0 as the buffer size (unbuffered)
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    #parse argumets, load config
    args = parse_args()
    config = load_config(args.config, args.section.replace('/',''))
    
    # debug mode
    if args.debug:
        print '-----'
        print 'args: {0}'.format(args)
        print 'config: {0}'.format(config)
        print 'function name: {0}'.format(args.func.__name__)
        print '-----'

    # ignore change directory for some functions
    if config['workdir'] and args.func.__name__ not in ('show'):
        change_directory(config['workdir'])

    args.func(args, config)

if __name__ == '__main__':
    main()
