import socketserver
from .client import Client

QUIXPOSE_TCP_HOST = "tcp.quixpose.io"

class ExposedTCPServer(socketserver.TCPServer):
    def __init__(self, *args, **kwargs):
        self._qxp_client = Client()
        self._qxp_epid, self._qxp_port = self._qxp_client.get_endpoint()
        self.exposed_endpoint = QUIXPOSE_TCP_HOST, self._qxp_port
        super().__init__(*args, **kwargs)
