"""Announce myself on the network and listen for other nodes.

Requirement covered: dynamic discovery
Owner: (assign a group member)

What goes here:
- Periodic UDP announcement
- Keep a list of known nodes, remove ones that stop announcing
"""

"""Dynamic discovery over UDP broadcast. No fixed IPs, no registry.

1. A new node broadcasts HELLO with its role and unicast port (a few times, UDP can drop packets).
2. Every controller that hears it adds the sender and replies directly with PEER_LIST:
   its own entry, all peers it knows, and the current leader.
3. The new node merges that list into its membership table.
"""

import threading
import time

from common import messages

HELLO_REPEATS = 3
HELLO_GAP = 0.5      # seconds between repeated HELLOs


class Discovery:
    def __init__(self, node):
        self.node = node
        node.on(messages.HELLO, self.handle_hello)
        node.on(messages.PEER_LIST, self.handle_peer_list)

    def start(self) -> None:
        threading.Thread(target=self._announce, daemon=True).start()

    def _announce(self) -> None:
        for _ in range(HELLO_REPEATS):
            self.node.broadcast(self.node.make(messages.HELLO, role=self.node.role, port=self.node.port))
            time.sleep(HELLO_GAP)

    def handle_hello(self, msg: dict, addr) -> None:
        peer_addr = (addr[0], msg["port"])            # IP from the packet, port from the message
        if self.node.membership.add_or_update(msg["sender"], peer_addr, msg["role"]):
            print(f"[{self.node.node_id}] discovered {msg['sender']} ({msg['role']}) at {peer_addr}")

        if self.node.role != "controller":
            return                                    # only controllers answer
        reply = self.node.make(
            messages.PEER_LIST,
            me={"id": self.node.node_id, "port": self.node.port, "role": self.node.role},
            peers=self.node.membership.as_wire_list(),
            leader=self.node.membership.leader_id,
        )
        self.node.send(reply, peer_addr)

    def handle_peer_list(self, msg: dict, addr) -> None:
        me = msg["me"]
        m = self.node.membership
        if m.add_or_update(me["id"], (addr[0], me["port"]), me["role"]):
            print(f"[{self.node.node_id}] discovered {me['id']} ({me['role']}) via PEER_LIST")
        for p in msg["peers"]:
            if m.add_or_update(p["id"], p["addr"], p["role"]):
                print(f"[{self.node.node_id}] learned about {p['id']} ({p['role']}) from {me['id']}")
        if msg.get("leader") and m.leader_id is None:
            m.leader_id = msg["leader"]