import logging
from .client import Client

TUNNEL_ARG_DST_HOST = "dst_host"
TUNNEL_DEFAULT_DST_HOST = "localhost"
TUNNEL_ARG_DST_PORT = "dst_port"
TUNNEL_DEFAULT_DST_PORT = 80
TUNNEL_ARG_LOGGER = "logger"
TUNNEL_DEFAULT_LOG_APP = "quixpose"

class Tunnel:
    def __init__(self, **kwargs):
        # Load destination host
        self.dst_host = TUNNEL_DEFAULT_DST_HOST
        if TUNNEL_ARG_DST_HOST in kwargs:
            self.dst_host = kwargs[TUNNEL_ARG_DST_HOST]
        # Load destination port
        self.dst_port = TUNNEL_DEFAULT_DST_PORT
        if TUNNEL_ARG_DST_PORT in kwargs:
            self.dst_port = kwargs[TUNNEL_ARG_DST_PORT]
        if TUNNEL_ARG_LOGGER in kwargs:
            self.logger = kwargs[TUNNEL_ARG_LOGGER]
        else:
            self.logger = logging.getLogger(TUNNEL_DEFAULT_LOG_APP)
    
    def run_blocking(self):
        raise NotImplementedError
