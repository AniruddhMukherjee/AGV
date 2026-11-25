"""Shared helpers for sending and receiving over sockets.

Requirement covered: all (foundation)
Owner: (assign a group member)

What goes here:
- Send/receive a full message over TCP
- Helpers for UDP send/receive
"""




"""Small socket helpers so every module opens sockets the same way."""

import socket

from common import messages
from common.settings import BROADCAST_ADDR, BUFFER_SIZE, DISCOVERY_PORT


def udp_broadcast_socket(port: int = DISCOVERY_PORT) -> socket.socket:
    """UDP socket that can send and receive broadcasts.
    Several processes on one machine can bind the same port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):          # not on Windows
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", port))
    return sock


def udp_socket() -> socket.socket:
    """Plain UDP socket on a free port, for direct node-to-node messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 0))
    return sock


def send(sock: socket.socket, msg: dict, addr: tuple) -> None:
    sock.sendto(messages.encode(msg), addr)


def broadcast(sock: socket.socket, msg: dict, port: int = DISCOVERY_PORT) -> None:
    sock.sendto(messages.encode(msg), (BROADCAST_ADDR, port))


def receive(sock: socket.socket) -> tuple[dict, tuple]:
    """Block until one valid message arrives. Returns (message, sender_address)."""
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        try:
            return messages.decode(data), addr
        except ValueError:
            continue    # ignore junk on the port