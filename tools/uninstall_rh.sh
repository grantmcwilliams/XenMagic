#!/bin/bash
# Uninstall script for Redhat systems

#Stop the service
if [[ -e /etc/init.d/xenmagic ]] ;then
	/etc/init.d/xenmagic stop
	/sbin/chkconfig --del xenmagic
fi

#Delete the xenwm user
if grep xenwm /etc/passwd ;then 
	userdel  xenwm
fi

#Delete everything else
if [[ -d /usr/share/xenmagic ]] ;then
	rm -Rf /usr/share/xenmagic/
fi
if [[ -e /etc/init.d/xenmagic ]] ;then
	rm /etc/init.d/xenmagic 
fi
if [[ -d /etc/xenmagic ]] ;then
	rm -Rf /etc/xenmagic/
fi
if [[ -d /var/log/xenmagic ]] ;then
	rm -Rf /var/log/xenmagic
fi
if [[ -d /var/lib/xenmagic ]] ;then
	rm -Rf /var/lib/xenmagic
fi
if [[ -e /usr/bin/xenmagic ]];then
	rm -f /usr/bin/xenmagic
fi

