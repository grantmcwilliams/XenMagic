#!/bin/bash
# Install script for Redhat Systems

PROGNAME="xenmagic"
INSTALLDIR="/usr/share/${PROGNAME}"
CONFIGDIR="/etc/${PROGNAME}"
LOGDIR="/var/log/${PROGNAME}"
LIBDIR="/var/lib/${PROGNAME}"
PROGUSER="xenwm"

#Stop the service
if [[ -e "/etc/init.d/${PROGNAME}" ]] ;then
	"/etc/init.d/${PROGNAME}" stop
	/sbin/chkconfig --del "${PROGNAME}"
fi

#Delete the xenwm user
if grep "${PROGUSER}" /etc/passwd ;then 
	userdel "${PROGUSER}"
fi

#Delete everything else
for ITEM in "${INSTALLDIR}" "/etc/init.d/${PROGNAME}" "${CONFIGDIR}" "${LOGDIR}" "${LIBDIR}" "/usr/bin/${PROGNAME}" ;do
	rm -Rf "${ITEM}"
done
