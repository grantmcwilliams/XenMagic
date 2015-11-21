#!/bin/bash
# Install script for Redhat Systems

PROGNAME="xenmagic"
INSTALLDIR="/usr/share/${PROGNAME}"
CONFIGDIR="/etc/${PROGNAME}"
LOGDIR="/var/log/${PROGNAME}"
LIBDIR="/var/lib/${PROGNAME}"
PROGUSER="xenwm"
DEPENDENCIES="epel-release python-cherrypy python-configobj"


# Check if user has administrative privileges 
if [[ "${EUID}" ! -eq 0 ]] ;then
	echo "Error: root privileges necessary to install - exiting"
	exit 1
fi

# Check dependencies
for RPM in ${DEPENDENCIES} ; do	
	if ! rpm -q "${RPM}" ;then
		echo "Error: ${RPM} needed for $PROGNAME to run - exiting"
		exit 1		
	fi
done

# install XenMagic to INSTALLDIR
if [[ ! -d "${INSTALLDIR}" ]] ;then
	if mkdir "${INSTALLDIR}" ;then
		chmod 775 "${INSTALLDIR}"
	else
		echo "Error: Unable to create ${INSTALLDIR}"
	fi
else
	cp -a ../* "${INSTALLDIR}"
fi

# Install sysv service file
if [[ -e ./xenmagic ]] ;then
	cp ./xenmagic "/etc/init.d/"
	if /sbin/chkconfig --add xenmagic ;then
		echo "${PROGNAME} service added - to automatically start it run"
		echo "     /sbin/chkconfig ${PROGNAME} on"
fi

# Create xenmagic config directory and copy configs
if [[ ! -d "${CONFIGDIR}" ]] ;then
	mkdir "${CONFIGDIR}"
	chmod 770 "${CONFIGDIR}"
	cp ../cherry.conf "${CONFIGDIR}"
	cp ../frontend.conf "${CONFIGDIR}"
fi

# Create log dir
if [[ ! -d "${LOGDIR}" ]] ;then
	mkdir "${LOGDIR}"
	chmod 770 "${LOGDIR}"
fi

# Create lib dir
if [[ ! -d "${LIBDIR}" ]] ;then
	mkdir "${LIBDIR}"
	chmod 770 "${LIBDIR}"
fi


if [[ ! -L "/usr/bin/${PROGNAME}" ]] ;then
	ln -s "${INSTALLDIR}/frontend.py" "/usr/bin/${PROGNAME}"
fi

# Creating user
if ! grep "${PROGUSER}" /etc/passwd ;then
	useradd -M -d "${INSTALLDIR}" "${PROGUSER}" -s /sbin/nologin -r
	passwd -l "${PROGUSER}"
fi


chown -R "${PROGUSER}:${PROGUSER}" "${CONFIGDIR}"
chown -R "${PROGUSER}:${PROGUSER}" "${LOGDIR}"
chown -R "${PROGUSER}:${PROGUSER}" "${LIBDIR}"


