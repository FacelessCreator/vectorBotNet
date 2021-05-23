import http.server
import socketserver
import sys
import signal

ROOT_FOLDER = ''

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global ROOT_FOLDER
        if self.path == '/':
            self.path = 'index.html'
        self.path = ROOT_FOLDER + '/' + self.path
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def signal_handler(sig, frame):
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    if len(sys.argv) < 3:
        print("wrong args; use PORT ROOT_FOLDER")
        exit()
    PORT = int(sys.argv[1])
    ROOT_FOLDER = sys.argv[2]
    ROOT_FOLDER = ROOT_FOLDER.replace(" ", "%20")
    handler_object = MyHttpRequestHandler
    my_server = socketserver.TCPServer(("", PORT), handler_object)
    my_server.allow_reuse_address = True
    my_server.serve_forever()
