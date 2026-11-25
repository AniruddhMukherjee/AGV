"""Start one controller:   python -m controller --id 1"""

import argparse
import time

from controller.discovery import Discovery
from controller.heartbeat import Heartbeat
from controller.node import Node


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="controller number, e.g. 1")
    args = parser.parse_args()

    node = Node(f"C{args.id}", role="controller")
    discovery = Discovery(node)
    heartbeat = Heartbeat(node)
    # Later: election, multicast, state get created here the same way.

    node.start()
    discovery.start()
    heartbeat.start()
    print(f"[{node.node_id}] started, unicast port {node.port}")

    try:
        while True:
            time.sleep(5)
            members = sorted(node.membership.peers())
            print(f"[{node.node_id}] members: {[node.node_id] + members}  leader: {node.membership.leader_id}")
    except KeyboardInterrupt:
        node.stop()
        print(f"[{node.node_id}] stopped")


if __name__ == "__main__":
    main()