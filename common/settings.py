"""Shared settings. Change values here, not in individual modules."""

DISCOVERY_PORT = 50000          # UDP broadcast port for HELLO / PEER_LIST
BROADCAST_ADDR = "255.255.255.255"

HEARTBEAT_INTERVAL = 1.0        # seconds between heartbeats
HEARTBEAT_TIMEOUT = 3.0         # missed for this long -> node is unreachable

MIN_CONTROLLERS = 3             # needed for a majority after one failure
BUFFER_SIZE = 65535