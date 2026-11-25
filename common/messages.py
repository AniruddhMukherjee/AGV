"""Message formats shared by every program.

Requirement covered: all (foundation)
Owner: (assign a group member)

What goes here:
- One function per message type (request, grant, deny, heartbeat, election, ok, coordinator, announce...)
- encode(message) -> bytes and decode(bytes) -> message, using JSON
"""



"""Message formats shared by every node.

Every message is a JSON object with at least:
    type    - one of the constants below
    sender  - node ID of the sender, e.g. "C1" or "A1"
    msg_id  - unique ID, used to drop duplicates
Other fields depend on the type (see the README message table).

Changing this file affects everyone: announce it in the group chat first.
"""

import json
import uuid

# Discovery
HELLO = "HELLO"
PEER_LIST = "PEER_LIST"
# Liveness
HEARTBEAT = "HEARTBEAT"
# Bully election
ELECTION = "ELECTION"
ANSWER = "ANSWER"
COORDINATOR = "COORDINATOR"
# Reservations
RESERVE = "RESERVE"
RELEASE = "RELEASE"
GRANT = "GRANT"
DENY = "DENY"
# Ordered multicast
SEQ = "SEQ"
ACK = "ACK"
NACK = "NACK"
CATCHUP = "CATCHUP"

ALL_TYPES = {
    HELLO, PEER_LIST, HEARTBEAT, ELECTION, ANSWER, COORDINATOR,
    RESERVE, RELEASE, GRANT, DENY, SEQ, ACK, NACK, CATCHUP,
}


def make(msg_type: str, sender: str, **fields) -> dict:
    """Build a message dict. Example: make(RESERVE, "A1", zone="Z3")"""
    if msg_type not in ALL_TYPES:
        raise ValueError(f"unknown message type: {msg_type}")
    return {"type": msg_type, "sender": sender, "msg_id": uuid.uuid4().hex, **fields}


def encode(msg: dict) -> bytes:
    return json.dumps(msg).encode("utf-8")


def decode(data: bytes) -> dict:
    msg = json.loads(data.decode("utf-8"))
    if msg.get("type") not in ALL_TYPES:
        raise ValueError(f"unknown message type: {msg.get('type')}")
    return msg