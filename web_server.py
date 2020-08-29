
######
#stackoverflow.com/a/18543710
fwFolder = "/home/sfm/fw"
# fwFile = "node-rev-1.bin"


try:
    import http.server as BaseHTTPServer  # Python 3.x
except ImportError:
    import BaseHTTPServer  # Python 2.x

import os
import shutil
import sys

# FILEPATH = os.path.abspath(fwFile)
# FILEPATH = sys.argv[1] if sys.argv[1:] else __file__

class SimpleHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        ####
        ##testing...
        print ("self path ", self.path)
        # FILEPATH = os.path.abspath(self.path)
        FILEPATH = fwFolder+self.path
        print ("file path", FILEPATH)
        ###

        with open(FILEPATH, 'rb') as f:
            self.send_response(200)
            self.send_header("Content-Type", 'application/octet-stream')
            self.send_header("Content-Disposition", 'attachment; filename="{}"'.format(os.path.basename(FILEPATH)))
            fs = os.fstat(f.fileno())
            self.send_header("Content-Length", str(fs.st_size))
            self.end_headers()
            shutil.copyfileobj(f, self.wfile)

def test(HandlerClass=SimpleHTTPRequestHandler,
         ServerClass=BaseHTTPServer.HTTPServer,
         protocol="HTTP/1.0"):
    if sys.argv[2:]:
        port = int(sys.argv[2])
    else:
        port = 8000
    server_address = ('', port)

    HandlerClass.protocol_version = protocol
    httpd = BaseHTTPServer.HTTPServer(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    # print("Serving HTTP on {0[0]} port {0[1]} ... {1}".format(sa, FILEPATH))
    print("Web Server HTTP on {0[0]} port {0[1]}".format(sa))
    httpd.serve_forever()

if __name__ == '__main__':
    test()
