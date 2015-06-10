#!/bin/sh -x
# Workdir: /home/builder/build

# Build package
[ ! -d 'DEBS' ] && mkdir -p DEBS
fakeroot dpkg-deb --build debian DEBS
