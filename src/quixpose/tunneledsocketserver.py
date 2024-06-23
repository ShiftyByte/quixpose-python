import socketserver
import time
from threading import Thread
from .tunnel import Tunnel
from loguru import logger

QUIXPOSE_TCP_HOST = "tcp.quixpose.io"
QUIXPOSE_TIMEOUT = 6

class TunneledTCPServer(socketserver.TCPServer):
    def __init__(self, *args, **kwargs):
        dest_host, dest_port = args[0]
        self._qxp_tunnel = Tunnel(dst_host="localhost", dst_port=dest_port, logger=logger)
        self._qxp_thread = Thread(target=self._qxp_tunnel.run_blocking, daemon=True)
        self._qxp_thread.start()
        # wait a few seconds to get remote endpoint info
        timeout = QUIXPOSE_TIMEOUT
        while not self._qxp_tunnel.is_up:
            time.sleep(1)
            timeout -= 1
            if timeout <= 0:
                raise ConnectionError
        # all is good, set variables
        self.exposed_endpoint = QUIXPOSE_TCP_HOST, self._qxp_tunnel.endpoint_port
        super().__init__(*args, **kwargs)
