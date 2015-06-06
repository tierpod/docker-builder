#!/bin/sh -x
# Workdir: /home/builder/build

# Get metadata from control file
PACKAGE=$(awk '/Package/ {print $2}' debian/DEBIAN/control)
VERSION=$(awk '/Version/ {print $2}' debian/DEBIAN/control)
ARCH=$(awk '/Architecture/ {print $2}' debian/DEBIAN/control)

# Build package
[ ! -d 'DEBS' ] && mkdir -p DEBS
fakeroot dpkg-deb --build debian DEBS
