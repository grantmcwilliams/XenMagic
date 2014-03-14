#!/bin/bash
# Install script for Redhat Systems

if [[ ! -d /usr/share/xenmagic ]];then
	mkdir /usr/share/xenmagic/
fi
if [[ -d /usr/share/xenmagic ]] ;then
	chmod 775 /usr/share/xenmagic/
	cp -a ../* /usr/share/xenmagic/
fi

if [[ -e xenmagic ]] ;then
	cp xenmagic /etc/init.d/
	/sbin/chkconfig --add xenmagic
	/sbin/chkconfig xenmagic on
fi

if [[ ! -d /etc/xenmagic ]] ;then
	mkdir /etc/xenmagic/
	chmod 770 /etc/xenmagic
	cp ../cherry.conf /etc/xenmagic/
	cp ../frontend.conf /etc/xenmagic/
fi
if [[ ! -d /var/log/xenmagic ]] ;then
	mkdir /var/log/xenmagic
	chmod 770 /var/log/xenmagic
fi
if [[ ! -d /var/lib/xenmagic ]] ;then
	mkdir /var/lib/xenmagic
	chmod 770 /var/lib/xenmagic
fi

if [[ ! -L /usr/bin/xenmagic ]] ;then
	ln -s /usr/share/xenmagic/frontend.py /usr/bin/xenmagic
fi

# Creating user
if ! grep xenwm /etc/passwd ;then
	useradd -M -d /usr/share/xenmagic/ xenwm -s /sbin/nologin -r
	passwd -l xenwm
fi


chown -R xenwm:xenwm /etc/xenmagic/
chown -R xenwm:xenwm /var/log/xenmagic/ 
chown -R xenwm:xenwm /var/lib/xenmagic/ 

