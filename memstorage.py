import cgi
import cherrypy
import httplib
import time

class MemoryStorage(cgi.FieldStorage):
    importhost = None
    importpath = None
    def __init__(self, *args, **kwds):
        try:
            cgi.FieldStorage.__init__(self, *args, **kwds)
            """
            if kwds.get("headers") and not kwds["headers"]['Referer'].count("importvm"):
                cgi.FieldStorage.__init__(self, *args, **kwds)
            else:
                print args
            """
        except ValueError, ex:
            if str(ex) == 'Maximum content length exceeded':
                raise cherrypy.HTTPError(status=413)
            else:
                raise ex

    def read_lines_to_eof(self):
        """Internal: read lines until EOF."""
        while 1:
            line = self.fp.readline(1<<16)
            if not line:
                self.done = -1
                break
            self.__write(line)
    
    def read_lines_to_outerboundary(self):
        """Internal: read lines until outerboundary."""
        h = None
        next = "--" + self.outerboundary
        last = next + "--"
        delim = ""
        last_line_lfend = True
        d = time.localtime()

        while 1:
            line = self.fp.readline(1024)
            if not line:
                self.done = -1
                break


            if line[:2] == "--" and last_line_lfend:
                strippedline = line.strip()
                if strippedline == next:
                    break
                if strippedline == last:
                    self.done = 1
                    break
            odelim = delim
            if line[-2:] == "\r\n":
                delim = "\r\n"
                line = line[:-2]
                last_line_lfend = True
            elif line[-1] == "\n":
                delim = "\n"
                line = line[:-1]
                last_line_lfend = True
            else:
                delim = ""
                last_line_lfend = False
            if not h:
                h = httplib.HTTPConnection(self.importhost, 80)
                h.putrequest('PUT', self.importpath)
                h.putheader('User-Agent', 'put.py/1.0')
                h.putheader('Connection', 'keep-alive')
                h.putheader('Transfer-Encoding', 'chunked')
                h.putheader('Expect', '100-continue')
                h.putheader('Accept', '*/*')
                h.endheaders()
            h.send(odelim + line)

    def __write(self, h, line):
        if self.__file is not None:
            if self.__file.tell() + len(line) > 1000:
                h.write(self.__file.getvalue())
                self.__file = None
        h.write(line)
  
    def skip_lines(self):
        """Internal: skip lines until outer boundary if defined."""
        if not self.outerboundary or self.done:
            return
        next = "--" + self.outerboundary
        last = next + "--"
        last_line_lfend = True
        while 1:
            line = self.fp.readline(1<<16)
            if not line:
                self.done = -1
                break
            if line[:2] == "--" and last_line_lfend:
                strippedline = line.strip()
                if strippedline == next:
                    break
                if strippedline == last:
                    self.done = 1
                    break
            if line.endswith('\n'):
                last_line_lfend = True
            else:
                last_line_lfend = False

