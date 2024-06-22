import logging
import socket
from threading import Thread
from .client import Client, ClientError

TUNNEL_DEFAULT_DST_HOST = "localhost"
TUNNEL_DEFAULT_DST_PORT = 80
TUNNEL_DEFAULT_LOG_APP = "quixpose"


class TunnelConnectionHandler:
    def __init__(self, client, source, dst_sock):
        self._got_close = False
        self._client = client
        self._source = source
        self._dst_sock = dst_sock
        # start socket recv thread, make sure its daemon so it dies on ctrl+c.
        self._sock_thread = Thread(target=self.process_outgoing, daemon=True)
        self._sock_thread.start()

    def process_outgoing(self):
        # get data, and send it in a loop
        try:
            data = self._dst_sock.recv(4096)
            while data:
                self._client.send(self._source, data)
                data = self._dst_sock.recv(4096)
        except ConnectionError:
            # remote connection reset, or something
            self.logger.info(f"[LOCAL] Connection Interrupted, Notifying upstream.")
        if not self._got_close:
            # closing down because of tcp socket
            self._client.send_disconnect(self._source)

    def process_incoming(self, data):
        # got data from upstream, send it into the socket
        self._dst_sock.sendall(data)
    
    def stop(self):
        # mark we already got close signal
        self._got_close = True
        # unstuck the recv()
        self._dst_sock.shutdown(socket.SHUT_RDWR)
        # close dst_sock
        self._dst_sock.close()

class Tunnel:
    def __init__(self, **kwargs):
        self._client = None
        # Load destination host
        self.dst_host = TUNNEL_DEFAULT_DST_HOST
        if "dst_host" in kwargs:
            self.dst_host = kwargs['dst_host']
        # Load destination port
        self.dst_port = TUNNEL_DEFAULT_DST_PORT
        if "dst_port" in kwargs:
            self.dst_port = kwargs['dst_port']
        if "logger" in kwargs:
            self.logger = kwargs['logger']
        else:
            self.logger = logging.getLogger(TUNNEL_DEFAULT_LOG_APP)
        # start connections dict
        self._connections = {}

    def on_connect(self, source):
        self.logger.info(f"[CONNECTION] From {source}")
        # connect to target
        dst_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            dst_sock.connect((self.dst_host, self.dst_port))
        except ConnectionError:
            # could not connect locally, send disconnect back to ws upstream
            self._client.send_disconnect(source)
            return
        # self.logger.debug(f"[TCP] connected to {self.dst_host}:{self.dst_port}")
        # create a tunnel connection handler
        self._connections[source] = TunnelConnectionHandler(self._client, source, dst_sock)
    
    def on_disconnect(self, source):
        self.logger.info(f"[DISCONNECT] From {source}")
        if source in self._connections:
            self._connections[source].stop()
            del self._connections[source]
    
    def on_recv(self, source, data):
        # self.logger.debug(f"[DATA] from {source}, {len(data)} bytes.")
        # check if the connection is comming for a previously established connection (crash or rerun of client)
        # try to reconnect.
        if source not in self._connections:
            # try to reconnect again
            self.on_connect(source)

        # if connection is up or reconnection worked, deliver the data
        if source in self._connections:
            self._connections[source].process_incoming(data)

    def run_blocking(self):
        self.logger.info(f"[TUNNEL] Starting tunnel to {self.dst_host}:{self.dst_port}")
        # get the client instance
        self._client = Client()
        # get an endpoint
        try:
            epid, remote_port = self._client.get_endpoint()
        except ClientError as e: 
            self.logger.error("[ERROR] Could not get an endpoint", exc_info=True)
            return
        self.logger.info(f"[ENDPOINT] {epid}")
        self.logger.success(f"[TUNNEL] Ready @ tcp.quixpose.io:{remote_port}")
        # connect to the controlling websocket
        self._client.connect(on_connect=self.on_connect, on_recv=self.on_recv, on_disconnect=self.on_disconnect)
        # we don't have anything to send at this point, so just let the client process
        self._client.process_blocking()
