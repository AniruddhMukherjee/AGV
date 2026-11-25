"""Send 'I am alive' messages and detect nodes that stopped.

Requirement covered: fault tolerance
Owner: (assign a group member)

What goes here:
- Send heartbeats on a timer
- Report a node as failed after a timeout
"""


"""Heartbeat failure detection.

Every HEARTBEAT_INTERVAL seconds a node:
  1. sends HEARTBEAT to every peer it knows, and
  2. removes any peer it hasn't heard from for HEARTBEAT_TIMEOUT seconds.

Other modules can react to a dead peer with:
    heartbeat.on_peer_dead(callback)      # callback(node_id, role)
Election will use this to notice a dead leader; state will use it to release a dead AGV's zones.
"""

import threading
import time

from common import messages
from common.settings import HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT


class Heartbeat:
    def __init__(self, node):
        self.node = node
        self._dead_callbacks = []
        node.on(messages.HEARTBEAT, self.handle_heartbeat)

    def on_peer_dead(self, callback) -> None:
        self._dead_callbacks.append(callback)

    def start(self) -> None:
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self) -> None:
        while self.node.running.is_set():
            beat = self.node.make(messages.HEARTBEAT, role=self.node.role, port=self.node.port)
            for node_id, peer in self.node.membership.peers().items():
                self.node.send(beat, peer["addr"])
            self._check_timeouts()
            time.sleep(HEARTBEAT_INTERVAL)

    def _check_timeouts(self) -> None:
        now = time.time()
        for node_id, peer in self.node.membership.peers().items():
            if now - peer["last_seen"] > HEARTBEAT_TIMEOUT:
                self.node.membership.remove(node_id)
                print(f"[{self.node.node_id}] {node_id} ({peer['role']}) missed heartbeats, removed")
                for callback in self._dead_callbacks:
                    try:
                        callback(node_id, peer["role"])
                    except Exception as e:
                        print(f"[{self.node.node_id}] error in peer-dead callback: {e}")

    def handle_heartbeat(self, msg: dict, addr) -> None:
        sender = msg["sender"]
        # A heartbeat from someone we don't know (e.g. we removed them during a network hiccup,
        # or missed their HELLO): add them back instead of ignoring them.
        if self.node.membership.add_or_update(sender, (addr[0], msg["port"]), msg["role"]):
            print(f"[{self.node.node_id}] {sender} ({msg['role']}) is back (heard its heartbeat)")
        else:
            self.node.membership.touch(sender)