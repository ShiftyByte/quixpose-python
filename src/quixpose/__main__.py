
import sys
from .tunnel import Tunnel

try:
    dst_host, dst_port = sys.argv[1].split(":")
    dst_port = int(dst_port)
except:
    print(f"Usage: python -m quixpose <local destination host>:<local destination port>\n", sys.argv[0])
    sys.exit(1)

t = Tunnel(dst_host=dst_host, dst_port=dst_port)
t.run_blocking()
