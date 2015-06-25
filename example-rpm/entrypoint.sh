#!/bin/sh -x
# Workdir: /home/builder/build

if [ -n "$TARGET" ] && [ -n "$RELEASE" ]; then
	# Download source
	if [ -d 'SOURCES' ] || mkdir SOURCES
	spectool -g -R SPECS/$TARGET
	# Build rpm package
	rpmbuild --define "release $RELEASE" -ba SPECS/$TARGET
else
	echo 'Usage: TARGET=project RELEASE=0 entrypoint.sh'
	exit 1
fi
