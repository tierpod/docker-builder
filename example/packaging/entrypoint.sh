#!/bin/sh -x
# Workdir: /home/builder/rpmbuild

if [ -n "$SPEC" ] && [ -n "$RELEASE" ]; then
	# Download source
	spectool -g -R SPECS/$SPEC
	# Build rpm package
	rpmbuild --define "release $RELEASE" -ba SPECS/$SPEC
else
	echo 'Usage: SPEC=default.spec RELEASE=0 entrypoint.sh'
	exit 1
fi
