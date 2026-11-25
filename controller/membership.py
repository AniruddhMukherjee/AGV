"""Membership table: who is in the cluster, where they are, when we last heard from them.

Discovery fills it, heartbeat updates last_seen, election sets leader_id.
All access goes through the lock because several threads use it.
"""

import threading
import time


class Membership:
    def __init__(self, own_id: str):
        self.own_id = own_id
        self.leader_id = None
        self._peers = {}                 # node_id -> {"addr": (ip, port), "role": str, "last_seen": float}
        self._lock = threading.Lock()

    def add_or_update(self, node_id: str, addr, role: str) -> bool:
        """Add a peer or refresh it. Returns True if the peer is new."""
        if node_id == self.own_id:
            return False
        with self._lock:
            is_new = node_id not in self._peers
            self._peers[node_id] = {"addr": tuple(addr), "role": role, "last_seen": time.time()}
            return is_new

    def touch(self, node_id: str) -> None:
        """Record that we just heard from this peer (used by heartbeat)."""
        with self._lock:
            if node_id in self._peers:
                self._peers[node_id]["last_seen"] = time.time()

    def remove(self, node_id: str) -> None:
        with self._lock:
            self._peers.pop(node_id, None)
            if self.leader_id == node_id:
                self.leader_id = None

    def get(self, node_id: str):
        with self._lock:
            peer = self._peers.get(node_id)
            return dict(peer) if peer else None

    def peers(self, role: str = None) -> dict:
        """Copy of the table, optionally only one role ("controller" or "agv")."""
        with self._lock:
            return {nid: dict(p) for nid, p in self._peers.items() if role is None or p["role"] == role}

    def as_wire_list(self) -> list:
        """Peer list in a JSON-friendly form, for PEER_LIST messages."""
        with self._lock:
            return [{"id": nid, "addr": list(p["addr"]), "role": p["role"]} for nid, p in self._peers.items()]