# AGV

Distributed traffic control for simulated Automated Guided Vehicles (AGVs).
Controller nodes keep a replicated reservation table of warehouse zones. AGVs
must reserve a zone before entering it. No middleware: discovery, election,
ordering and recovery are all written in our own code.

Course project, Distributed Systems, WS 2026/27, Group 03.

## Architecture (hybrid)
- **Client-server** between AGVs and controllers: AGVs send reservation requests, controllers grant or deny.
- **Peer-to-peer** among the controller nodes. One controller is elected leader (sequencer) with the bully algorithm.
- **Replicated state machine:** every controller holds a full copy of the reservation table and applies the same commands in the same order.

Diagram: `docs/architecture.png`

## How the requirements map to the code
| Requirement | What it does in this system | Where |
|---|---|---|
| Dynamic discovery *(done)* | New controllers and AGVs broadcast `HELLO` over UDP. Existing controllers reply with `PEER_LIST` (members + current leader). | `controller/discovery.py` |
| Leader election *(next)* | Bully election, run when the leader's heartbeats stop. Nodes are compared by *(last applied sequence number, node ID)*, so the node with the most up-to-date log wins. | `controller/election.py`, `controller/heartbeat.py` |
| Reliable ordered multicast *(to do)* | The leader gives each request a global sequence number and multicasts it. Followers apply entries strictly in order, buffer out-of-order ones, and send `NACK` for gaps. Duplicates are dropped by request ID. | `controller/multicast.py` |
| Fault tolerance *(heartbeat done)* | Heartbeat failure detection, leader failover, release of locks held by crashed AGVs, and log catch-up for restarted nodes. | `controller/state.py`, `controller/heartbeat.py` |

## Design rules (keep the replicas identical)
1. **Only the leader changes state.** Every change, including releasing a dead AGV's zones, is a sequenced command (`RESERVE`, `RELEASE`). No node changes its table on its own timeout.
2. **Grant only after a majority has the entry.** The leader replies to an AGV only after a majority of controllers have acknowledged the sequenced entry, so a grant survives a leader crash.
3. **Every leader has a term number.** Messages from an older term are ignored, so a restarted old leader can't hand out sequence numbers.
4. **No circular waiting.** *(Pick one and delete the other:)* an AGV reserves its whole path at once / AGVs reserve zones in a fixed global order.
5. **At least 3 controllers** so a majority still exists after one failure.

## Message types
| Message | From → To | Purpose |
|---|---|---|
| `HELLO` | any new node → broadcast | announce itself |
| `PEER_LIST` | controller → new node | current members and leader |
| `HEARTBEAT` | every node → every known peer | liveness (1 s interval, 3 s timeout) |
| `ELECTION` / `ANSWER` / `COORDINATOR` | controller ↔ controller | bully election |
| `RESERVE` / `RELEASE` | AGV → controller → leader | request or free a zone |
| `SEQ` | leader → followers | sequenced command |
| `ACK` / `NACK` | follower → leader | confirm entry / ask for missing entries |
| `GRANT` / `DENY` | controller → AGV | reply to a request |
| `CATCHUP` | restarted node → peers | "my last applied sequence is N, send the rest" |

Exact field formats: `common/messages.py`

## Status
| Part | File | State |
|---|---|---|
| Shared message formats, sockets, settings | `common/` | done |
| Controller node and message routing | `controller/node.py` | done |
| Membership table | `controller/membership.py` | done |
| Dynamic discovery | `controller/discovery.py` | done, tested with 4 nodes |
| Heartbeat failure detection | `controller/heartbeat.py` | done, tested (crash + restart) |
| Bully leader election | `controller/election.py` | next |
| Ordered multicast | `controller/multicast.py` | to do |
| Reservation table, catch-up | `controller/state.py` | to do |
| Simulated AGV | `agv/` | to do |
| Viewer | `viewer/` | optional |

## Layout
```
AGV/
├── common/
│   ├── messages.py      message types, make / encode / decode (JSON over UDP)
│   ├── net.py           UDP socket helpers (broadcast, send, receive)
│   └── settings.py      ports, heartbeat interval and timeout
├── controller/
│   ├── __main__.py      entry point: python -m controller --id N
│   ├── node.py          sockets, listener threads, routes messages by type
│   ├── membership.py    thread-safe peer table + leader_id
│   ├── discovery.py     HELLO / PEER_LIST
│   └── heartbeat.py     HEARTBEAT, timeout detection, on_peer_dead callbacks
├── agv/                 simulated vehicle (to do)
├── viewer/              optional display
├── tests/
└── docs/
```

### How the controller code fits together
- `Node` owns two UDP sockets: one bound to the shared discovery port (broadcasts) and one on a random free port (direct messages). A listener thread runs on each.
- Modules register handlers per message type with `node.on(TYPE, handler)`; the node calls `handler(msg, addr)` for every matching message. New modules plug in the same way.
- `Membership` stores `node_id -> {addr, role, last_seen}` and `leader_id`. Discovery fills it, heartbeat refreshes and prunes it, election will set `leader_id`.
- `Heartbeat.on_peer_dead(callback)` lets other modules react to a crash (election: dead leader; state: release a dead AGV's zones).
- Node IDs: controllers are `C1`, `C2`, ...; AGVs will be `A1`, `A2`, ...

### Discovery
1. A new node broadcasts `HELLO` (role + its direct port) three times, 0.5 s apart, because UDP can drop packets.
2. Every controller that hears it adds the sender and replies directly with `PEER_LIST`: itself, every peer it knows, and the current leader.
3. The new node merges the list, so it also learns about peers whose `HELLO` replies it missed.

### Heartbeat
- Every `HEARTBEAT_INTERVAL` (1 s) each node sends `HEARTBEAT` to all known peers.
- A peer not heard from for `HEARTBEAT_TIMEOUT` (3 s) is removed and the `on_peer_dead` callbacks run.
- A heartbeat from an unknown node adds it back (covers a node dropped during a short network hiccup).
- A restarted node gets a new port; its `HELLO` updates the stored address.

## Team
| Member |
|---|
| Aniruddh Mukherjee |
| Anushka Mukherjee |
| Arishti Salaria |
| Anish Tangadpalliwar |

## Who owns what
| Part | Files | Owner |
|---|---|---|
| Discovery | `controller/discovery.py` | |
| Leader election and heartbeat | `controller/election.py`, `controller/heartbeat.py` | |
| Ordered multicast | `controller/multicast.py` | |
| Fault tolerance, state, AGV | `controller/state.py`, `agv/` | |
| Shared code | `common/`, `controller/node.py`, `controller/membership.py` | everyone, changes agreed in the group chat |

## Working rules
For now everyone works on `main` (no separate branches yet).
1. Pull the latest `main` before you start work each day: `git pull origin main`.
2. Pull again right before you push, so you don't overwrite someone else's work.
3. Only edit your own files unless you have agreed it in the group chat first.
4. Changes to shared code (`common/`, `node.py`, `membership.py`) affect everyone: announce them before pushing.
5. Only push code that runs: start 3 controllers and check nothing broke.
6. Write short commit messages that say what changed.

Once several people are coding at the same time, switch to one branch per person and pull requests reviewed by at least one other member.

## Requirements
- Python 3 (developed and tested on Windows)
- Standard library only, no middleware

## Running
From the repo root, one terminal per controller:
```
python -m controller --id 1
python -m controller --id 2
python -m controller --id 3
```
Each node prints its member list every 5 seconds. Always use `python -m controller`; running `controller/__main__.py` directly breaks the `common` imports.

### Windows notes
- Allow Python through Windows Defender Firewall the first time, or broadcasts are blocked.
- Discovery needs an active network adapter (Wi-Fi on). A VPN or virtual adapters (Hyper-V, WSL, Docker) can send broadcasts out the wrong interface.
- Several nodes share the discovery port via `SO_REUSEADDR` (and `SO_REUSEPORT` where it exists).
- After sending UDP to a crashed peer's port, Windows makes the next receive fail with `ConnectionResetError` (WinError 10054). `node.py` ignores it; without that, one dead peer made a node stop receiving entirely.

## Tests done so far
| Test | Result |
|---|---|
| One controller alone | starts, lists only itself |
| Three controllers | all list all three, no IPs configured |
| Fourth controller joins late | everyone lists it, it lists everyone |
| Kill one controller | the others remove only that node within ~3 s |
| Restart it | rejoins on a new port, nobody removed afterwards |
| Kill two of three | the survivor removes both |

## Demo scenarios (target)
1. Start 3 controllers and 2 AGVs; they find each other with no IPs configured.
2. Two AGVs request the same zone at the same moment; exactly one gets it, and every replica agrees.
3. Kill the leader; a new one is elected and existing reservations are kept.
4. Kill an AGV; its zones are released.
5. Restart a crashed controller; it catches up on the log before serving requests.