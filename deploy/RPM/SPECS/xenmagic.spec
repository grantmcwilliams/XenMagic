# $Id$
# Authority: arrfab

Summary: XenMagic is a web-based open source clone of Xencenter
Name: xenmagic
Version: 1.0b3
Release: 1%{?dist}
License: GPL
Group: Applications/System
URL: http://xenmagic.com

Source: http://xenmagic.com/phocadownload/Tarballs/xenmagic-1.0b-3.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildArch: noarch

Requires: python >= 2.4
Requires: python-cherrypy >= 3.1
Requires: python-mako >= 0.3.4
Requires: python-simplejson >= 2.0.5
Requires: graphviz

%description
XenMagic is a web-based open source clone of Xencenter. With XenMagic you only need a browser for manage your server and virtual machines running on XenServers

%prep
%setup -q -n xenmagic

# Defining a default initscript
%{__cat} <<'EOF' >tools/magic.init
#!/bin/sh
#
# xenmagic:        Start/stop xenmagic service
#
# chkconfig:    2345 25 90
# description: XenMagic is a web-based open source clone of Xencenter.
#


# Source function library.
. /etc/rc.d/init.d/functions

start()
{
        echo -n $"Starting XenMagic service:"
        daemon --user=xenwm  /usr/bin/xenmagic -daemon
        PID=$(/bin/ps -ef|/bin/grep frontend.py|/bin/grep -v grep|/bin/awk '{print $2}')
        echo $PID > /var/run/xenmagic.pid
        echo ""
}

stop()
{
        echo -n "Stopping XenMagic service:"
        killproc -p /var/run/xenmagic.pid xenmagic 
        echo ""
}

xwmstatus()
{
        status -p /var/run/xenmagic.pid xenmagic
        echo ""
}

case "$1" in
  start)
        start
        ;;
  stop)
        stop
        ;;
  restart|reload)
        stop
        start
        ;;
  condrestart)
        [ -e /var/lock/subsys/xenmagic ] && (stop; start)
        ;;
  status)
        xwmstatus 
        ;;
  *)
        echo $"Usage: $0 {start|stop|status|restart|reload|condrestart}"
        exit 1
        ;;
esac

exit 0
EOF

### Adds a shell wrapper script for xenmagic.
%{__cat} <<EOF >xenmagic.wrapper
#!/bin/bash
cd %{_datadir}/xenmagic
python frontend.py -daemon >/dev/null 2>&1
EOF


%build


%install
%{__rm} -rf %{buildroot}
%{__install} -d -m0755 %{buildroot}%{_datadir}/xenmagic
%{__cp} -av * %{buildroot}/usr/share/xenmagic
%{__install} -D -m0755 tools/xenmagic.init %{buildroot}%{_initrddir}/xenmagic
%{__install} -d -m0755 %{buildroot}%{_sysconfdir}/xenmagic
%{__install} -m0644 cherry.conf %{buildroot}%{_sysconfdir}/xenmagic/
%{__install} -m0644 frontend.conf %{buildroot}%{_sysconfdir}/xenmagic/
%{__install} -D -d -m0755 %{buildroot}%{_localstatedir}/log/xenmagic
%{__install} -D -d -m0755 %{buildroot}%{_localstatedir}/lib/xenmagic
%{__install} -D -m0755 xenmagic.wrapper %{buildroot}%{_bindir}/xenmagic

%pre
if ! /usr/bin/id xenwm &>/dev/null; then
    /usr/sbin/useradd -r -d /usr/share/xenmagic -s /sbin/nologin -c "xenmagic" xenwm || \
        %logmsg "Unexpected error adding user \"xenwm\". Aborting installation."
fi

%post
/sbin/chkconfig --add xenmagic

%preun
if [ $1 = 0 ]; then
        /sbin/service xenmagic stop > /dev/null 2>&1
        /sbin/chkconfig --del xenmagic
fi

%postun
if [ $1 -eq 0 ]; then
    /usr/sbin/userdel xenwm || %logmsg "User \"xenwm\" could not be deleted."
fi

%clean
%{__rm} -rf %{buildroot}

%files
%defattr(-, root, root, 0755)
#%doc LICENSE README
%dir %{_datadir}/xenmagic/
%{_datadir}/xenmagic/*
%dir %{_sysconfdir}/xenmagic/
%{_initrddir}/xenmagic
%{_bindir}/xenmagic

%defattr(-, xenwm, xenwm, 0755 )
%{_localstatedir}/lib/xenmagic/
%{_localstatedir}/log/xenmagic/
%config(noreplace) %{_sysconfdir}/xenmagic/frontend.conf
%config(noreplace) %{_sysconfdir}/xenmagic/cherry.conf


%changelog
* Mon Mar 17 2014 Grant McWilliams <grant@soundlinuxtraining.com> - 1.0b-3
- Revised specfile for renaming of xenwebmanager to xenmagic
* Sun Oct 24 2010 Fabian Arrotin <fabian.arrotin@arrfab.net> - 0.9.1-1
- Initial package



