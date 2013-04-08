#!/bin/bash
mkdir /usr/share/xenwebmanager/
chmod 775 /usr/share/xenwebmanager/
cp -a ../* /usr/share/xenwebmanager/
cp xenwebmanager /etc/init.d/
/sbin/chkconfig --add xenwebmanager
/sbin/chkconfig xenwebmanager on
mkdir /etc/xenwebmanager/
mkdir /var/log/xenwebmanager
mkdir /var/lib/xenwebmanager
chmod 770 /etc/xenwebmanager
chmod 770 /var/log/xenwebmanager
chmod 770 /var/lib/xenwebmanager
cp ../cherry.conf /etc/xenwebmanager/
cp ../frontend.conf /etc/xenwebmanager/
ln -s /usr/share/xenwebmanager/frontend.py /usr/bin/xenwebmanager

# Creating user
useradd -M -d /usr/share/xenwebmanager/ xenwm -s /sbin/nologin -r
passwd -l xenwm

chown xenwm:xenwm /etc/xenwebmanager/ -R
chown xenwm:xenwm /var/log/xenwebmanager/ -R
chown xenwm:xenwm /var/lib/xenwebmanager/ -R

