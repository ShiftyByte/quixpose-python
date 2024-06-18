import sys
import argparse
from loguru import logger
from .tunnel import Tunnel

parser = argparse.ArgumentParser(prog='python -m quixpose', description="Quixpose Tunneling Client")
parser.add_argument("dest", metavar="host:port", help="Destination Host:Port to tunnel traffic to")
args = parser.parse_args()

try:
    dst_host, dst_port = args.dest.split(":")
    dst_port = int(dst_port)
except ValueError:
    parser.print_help()
    sys.exit(1)

t = Tunnel(dst_host=dst_host, dst_port=dst_port, logger=logger)
t.run_blocking()
