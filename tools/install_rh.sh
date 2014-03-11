#!/bin/bash
mkdir /usr/share/xenmagic/
chmod 775 /usr/share/xenmagic/
cp -a ../* /usr/share/xenmagic/
cp xenmagic /etc/init.d/
/sbin/chkconfig --add xenmagic
/sbin/chkconfig xenmagic on
mkdir /etc/xenmagic/
mkdir /var/log/xenmagic
mkdir /var/lib/xenmagic
chmod 770 /etc/xenmagic
chmod 770 /var/log/xenmagic
chmod 770 /var/lib/xenmagic
cp ../cherry.conf /etc/xenmagic/
cp ../frontend.conf /etc/xenmagic/
ln -s /usr/share/xenmagic/frontend.py /usr/bin/xenmagic

# Creating user
useradd -M -d /usr/share/xenmagic/ xenwm -s /sbin/nologin -r
passwd -l xenwm

chown xenwm:xenwm /etc/xenmagic/ -R
chown xenwm:xenwm /var/log/xenmagic/ -R
chown xenwm:xenwm /var/lib/xenmagic/ -R

