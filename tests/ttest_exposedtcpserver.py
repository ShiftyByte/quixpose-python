import socketserver
from quixpose import ExposedTCPServer
from threading import Thread
import uuid
import socket


RANDOM_DATA = uuid.uuid4().bytes

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024)
        # just send back the same data, but reversed
        self.request.sendall(self.data[::-1])


def client_thread(host,port):
    s = socket.socket()
    s.connect((host, port))
    s.sendall(RANDOM_DATA)
    returned_data = s.recv(1024)
    assert returned_data[::-1] == RANDOM_DATA


def test_exposed_tcp_server():
    HOST, PORT = "localhost", 9999

    with ExposedTCPServer((HOST, PORT), MyTCPHandler) as server:
        qxp_host, qxp_port = server.exposed_endpoint
        client = Thread(target=client_thread, args=(qxp_host, qxp_port))
        server.serve_forever()
