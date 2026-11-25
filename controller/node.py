"""The main controller program. Starts and connects all the other parts.

Requirement covered: architectural model
Owner: (assign a group member)

What goes here:
- Start the discovery, heartbeat, election and multicast parts
- Accept connections from AGVs and forward their requests to the leader
- Run with: python3 -m controller.node
"""



"""One controller process: owns the sockets, the membership table and the message router.

Modules (discovery, heartbeat, election, ...) register a handler per message type:
    node.on(messages.HELLO, self.handle_hello)
Handlers are called as handler(msg, addr).
"""

import threading

from common import messages, net


class Node:
    def __init__(self, node_id: str, role: str = "controller"):
        from controller.membership import Membership

        self.node_id = node_id
        self.role = role
        self.membership = Membership(node_id)

        self.unicast = net.udp_socket()               # direct node-to-node messages
        self.port = self.unicast.getsockname()[1]
        self.discovery_sock = net.udp_broadcast_socket()

        self._handlers = {}
        self.running = threading.Event()

    # --- routing ---------------------------------------------------------
    def on(self, msg_type: str, handler) -> None:
        self._handlers.setdefault(msg_type, []).append(handler)

    def _dispatch(self, msg: dict, addr) -> None:
        if msg.get("sender") == self.node_id:
            return                                    # our own broadcast echoed back
        for handler in self._handlers.get(msg["type"], []):
            try:
                handler(msg, addr)
            except Exception as e:                    # one bad message must not kill the node
                print(f"[{self.node_id}] error handling {msg['type']}: {e}")

    def _listen(self, sock) -> None:
        while self.running.is_set():
            try:
                msg, addr = net.receive(sock)
            except OSError:
                break                                 # socket closed on shutdown
            self._dispatch(msg, addr)

    # --- sending ---------------------------------------------------------
    def make(self, msg_type: str, **fields) -> dict:
        return messages.make(msg_type, self.node_id, **fields)

    def send(self, msg: dict, addr) -> None:
        net.send(self.unicast, msg, tuple(addr))

    def send_to(self, node_id: str, msg: dict) -> bool:
        peer = self.membership.get(node_id)
        if peer is None:
            return False
        self.send(msg, peer["addr"])
        return True

    def broadcast(self, msg: dict) -> None:
        net.broadcast(self.unicast, msg)

    # --- lifecycle -------------------------------------------------------
    def start(self) -> None:
        self.running.set()
        for sock in (self.unicast, self.discovery_sock):
            threading.Thread(target=self._listen, args=(sock,), daemon=True).start()

    def stop(self) -> None:
        self.running.clear()
        for sock in (self.unicast, self.discovery_sock):
            sock.close()