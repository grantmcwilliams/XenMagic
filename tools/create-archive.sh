#!/bin/bash

ARCDIR="../../XenMagic-archive"
PROJECT="../../XenMagic"
VERSIONFILE="${ARCDIR}/XenMagic/deploy/version"

# Create a copy of the project dir
cp -Rf ${PROJECT} ${ARCDIR}

# Remove .git project files and binary RPMs
rm -Rf ${ARCDIR}/XenMagic/.git
find ${ARCDIR} -type f -name "*.rpm" -exec rm -f {} \;

# Get the current release version
PROGVER=$(cat "${ARCDIR}/XenMagic/deploy/version")

echo "Current version string: $PROGVER"
echo "Desired version string:"
read NEWVER
if [[ ! -z "${NEWVER}" ]] ;then
	PROGVER="${NEWVER}" 
	echo "${PROGVER}" > "${VERSIONFILE}"
fi

# Create clean archive in ${ARCDIR}
tar -czvpf ../../xenmagic-${PROGVER}.tar.gz ${PROJECT}

# Move archive to project parent and delete ${ARCDIR}
rm -Rf ${ARCDIR}

