import socketserver
from quixpose import TunneledTCPServer
from threading import Thread
import uuid
import socket
import time


RANDOM_DATA = uuid.uuid4().bytes

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024)
        # just send back the same data, but reversed
        self.request.sendall(self.data[::-1])
        # leave after 1 second
        time.sleep(1)
        self.server.shutdown()


def client_thread(host, port, keep_running):
    s = socket.socket()
    print("connecting to", host, port)
    s.connect((host, port))
    s.sendall(RANDOM_DATA)
    print("sent", RANDOM_DATA)
    returned_data = s.recv(1024)
    print("recvd", returned_data)
    assert returned_data[::-1] == RANDOM_DATA
    print("exiting")
    s.close()
    keep_running[0] = False    


def test_exposed_tcp_server():
    HOST, PORT = "localhost", 9999

    with TunneledTCPServer((HOST, PORT), MyTCPHandler) as server:
        qxp_host, qxp_port = server.exposed_endpoint
        print(qxp_host, qxp_port)
        keep_running = [True]
        client = Thread(target=client_thread, args=(qxp_host, qxp_port, keep_running))
        client.run()
        server.serve_forever()
