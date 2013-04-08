import os
import re
try:
    set
except NameError:
    from sets import Set as set
import signal as _signal
import sys
import time
import threading
class SimplePlugin(object):
    """Plugin base class which auto-subscribes methods for known channels."""
    
    def __init__(self, bus):
        self.bus = bus
    
    def subscribe(self):
        """Register this object as a (multi-channel) listener on the bus."""
        for channel in self.bus.listeners:
            # Subscribe self.start, self.exit, etc. if present.
            method = getattr(self, channel, None)
            if method is not None:
                self.bus.subscribe(channel, method)
    
    def unsubscribe(self):
        """Unregister this object as a listener on the bus."""
        for channel in self.bus.listeners:
            # Unsubscribe self.start, self.exit, etc. if present.
            method = getattr(self, channel, None)
            if method is not None:
                self.bus.unsubscribe(channel, method)


class Daemonizer(SimplePlugin):
    """Daemonize the running script.
    
    Use this with a Web Site Process Bus via:
        
        Daemonizer(bus).subscribe()
    
    When this component finishes, the process is completely decoupled from
    the parent environment. Please note that when this component is used,
    the return code from the parent process will still be 0 if a startup
    error occurs in the forked children. Errors in the initial daemonizing
    process still return proper exit codes. Therefore, if you use this
    plugin to daemonize, don't use the return code as an accurate indicator
    of whether the process fully started. In fact, that return code only
    indicates if the process succesfully finished the first fork.
    """
    
    def __init__(self, bus, stdin='/dev/null', stdout='/dev/null',
                 stderr='/dev/null'):
        SimplePlugin.__init__(self, bus)
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.finalized = False
    
    def start(self):
        if self.finalized:
            self.bus.log('Already deamonized.')
        
        # forking has issues with threads:
        # http://www.opengroup.org/onlinepubs/000095399/functions/fork.html
        # "The general problem with making fork() work in a multi-threaded
        #  world is what to do with all of the threads..."
        # So we check for active threads:
        if threading.activeCount() != 1:
            self.bus.log('There are %r active threads. '
                         'Daemonizing now may cause strange failures.' %
                         threading.enumerate(), level=30)
        
        # See http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        # (or http://www.faqs.org/faqs/unix-faq/programmer/faq/ section 1.7)
        # and http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
        
        # Finish up with the current stdout/stderr
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Do first fork.
        try:
            pid = os.fork()
            if pid == 0:
                # This is the child process. Continue.
                pass
            else:
                # This is the first parent. Exit, now that we've forked.
                self.bus.log('Forking once.')
                os._exit(0)
        except OSError, exc:
            # Python raises OSError rather than returning negative numbers.
            sys.exit("%s: fork #1 failed: (%d) %s\n"
                     % (sys.argv[0], exc.errno, exc.strerror))
        
        os.setsid()
        
        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                self.bus.log('Forking twice.')
                os._exit(0) # Exit second parent
        except OSError, exc:
            sys.exit("%s: fork #2 failed: (%d) %s\n"
                     % (sys.argv[0], exc.errno, exc.strerror))
        
        #os.chdir("/")
        os.umask(0)
        
        si = open(self.stdin, "r")
        so = open(self.stdout, "a+")
        se = open(self.stderr, "a+", 0)

        # os.dup2(fd, fd2) will close fd2 if necessary,
        # so we don't explicitly close stdin/out/err.
        # See http://docs.python.org/lib/os-fd-ops.html
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        self.bus.log('Daemonized to PID: %s' % os.getpid())
        self.finalized = True
    start.priority = 65

