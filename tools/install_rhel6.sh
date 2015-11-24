#!/bin/bash
# Install script for Redhat Systems

PROGNAME="xenmagic"
INSTALLDIR="/usr/share/${PROGNAME}"
CONFIGDIR="/etc/${PROGNAME}"
LOGDIR="/var/log/${PROGNAME}"
LIBDIR="/var/lib/${PROGNAME}"
PROGUSER="xenwm"
DEPENDENCIES="epel-release python-cherrypy python-configobj"
PROGPATH="${PWD%/*}"

# exit function
cleanup()
{
	echo ""
	RES="${1}"
	if [[ ${RES} = 0 ]] ;then
		echo "${PROGNAME^} installed successfully"
	else
		echo "${PROGNAME^} installation failed"
		exit 1
	fi
}

# Check if user has administrative privileges 
if [[ ! "${EUID}" -eq '0' ]] ;then
	echo "Error: root privileges necessary to install - exiting"
	cleanup 1
fi

# Check dependencies
echo "Checking software dependencies"
for RPM in ${DEPENDENCIES} ; do	
	if ! rpm -q "${RPM}" &> /dev/null  ;then
		echo "Error: ${RPM} needed for $PROGNAME to run - exiting"
		clean 1		
	fi
done

# Create XenMagic INSTALLDIR
echo "Creating install directory: ${INSTALLDIR}"
if [[ ! -d "${INSTALLDIR}" ]] ;then
	if mkdir -p "${INSTALLDIR}" ;then
		chmod 775 "${INSTALLDIR}"
	else
		echo "Error: Unable to create ${INSTALLDIR}"
		cleanup 1
	fi
fi

# Copy XenMagic to INSTALLDIR
echo "Installing ${PROGNAME} to ${INSTALLDIR}"
if [[ -d "${INSTALLDIR}" ]] ;then
	if ! cp -a ${PROGPATH}/* "${INSTALLDIR}" ;then
		echo "Unable to copy ${PROGNAME} to ${INSTALLDIR}"
		cleanup 1
	fi
fi

# Install sysv service file
echo "Installing service file to /etc/init.d"
if [[ -e "${PROGPATH}/tools/xenmagic" ]] ;then
	if ! cp "${PROGPATH}/tools/xenmagic" "/etc/init.d/" ;then
		echo "Unable to copy service file ${PROGPATH}/tools/xenmagic to /etc/init.d"
		cleanup 1
	fi
	if ! /sbin/chkconfig --add xenmagic ;then
		echo "Unable to enable service"
		cleanup 1
	fi
fi

# Create XenMagic config directory
echo "Creating ${CONFIGDIR}"
if [[ ! -d "${CONFIGDIR}" ]] ;then
	mkdir -p "${CONFIGDIR}"
	chmod 770 "${CONFIGDIR}"
fi

# Copy XenMagic configs
echo "Copying config files to ${CONFIGDIR}"
if [[ -d "${CONFIGDIR}" ]] ;then
	for FILE in "${PROGPATH}/cherry.conf" "${PROGPATH}/frontend.conf" ; do
		if ! cp "${FILE}" "${CONFIGDIR}" ;then
			echo "Unable to copy ${FILE} to ${CONFDIDR}"
			cleanup 1
		fi
	done
fi

# Create log dir
echo "Creating ${LOGDIR}"
if [[ ! -d "${LOGDIR}" ]] ;then
	if ! mkdir -p "${LOGDIR}" ;then
		echo "Unable to create ${LOGDIR}"
		cleanup 1
	fi
	chmod 770 "${LOGDIR}"
fi

# Create lib dir
echo "Creating ${LIBDIR}"
if [[ ! -d "${LIBDIR}" ]] ;then
	if ! mkdir -p "${LIBDIR}" ;then
		echo "Unable to create ${LIBDIR}"
		cleanup 1
	fi
	chmod 770 "${LIBDIR}"
fi

# Create link
echo "Creating /usr/bin/${PROGNAME} link"
if [[ ! -L "/usr/bin/${PROGNAME}" ]] ;then
	if ! ln -s "${INSTALLDIR}/frontend.py" "/usr/bin/${PROGNAME}" ;then
		echo "Unable to create /usr/bin/${PROGNAME}"
		cleanup 1
	fi
fi

# Creating user
echo "Creating ${PROGUSER} user"
if ! grep -q "${PROGUSER}" /etc/passwd ;then
	useradd -M -d "${INSTALLDIR}" "${PROGUSER}" -s /sbin/nologin -r
	passwd -l "${PROGUSER}"
fi

# Set file ownership
chown -R "${PROGUSER}:${PROGUSER}" "${CONFIGDIR}"
chown -R "${PROGUSER}:${PROGUSER}" "${LOGDIR}"
chown -R "${PROGUSER}:${PROGUSER}" "${LIBDIR}"

echo ""
echo "${PROGNAME} service enabled - to automatically start it run"
echo "     /sbin/chkconfig ${PROGNAME} on"

cleanup 0

