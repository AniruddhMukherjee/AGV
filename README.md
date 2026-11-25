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
| Dynamic discovery | New controllers and AGVs broadcast `HELLO` over UDP. Existing controllers reply with `PEER_LIST` (members + current leader). | `controller/discovery.py` |
| Leader election | Bully election, run when the leader's heartbeats stop. Nodes are compared by *(last applied sequence number, node ID)*, so the node with the most up-to-date log wins. | `controller/election.py`, `controller/heartbeat.py` |
| Reliable ordered multicast | The leader gives each request a global sequence number and multicasts it. Followers apply entries strictly in order, buffer out-of-order ones, and send `NACK` for gaps. Duplicates are dropped by request ID. | `controller/multicast.py` |
| Fault tolerance | Heartbeat failure detection, leader failover, release of locks held by crashed AGVs, and log catch-up for restarted nodes. | `controller/state.py`, `controller/heartbeat.py` |

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
| `HEARTBEAT` | leader → followers, AGV → controller | liveness |
| `ELECTION` / `ANSWER` / `COORDINATOR` | controller ↔ controller | bully election |
| `RESERVE` / `RELEASE` | AGV → controller → leader | request or free a zone |
| `SEQ` | leader → followers | sequenced command |
| `ACK` / `NACK` | follower → leader | confirm entry / ask for missing entries |
| `GRANT` / `DENY` | controller → AGV | reply to a request |
| `CATCHUP` | restarted node → peers | "my last applied sequence is N, send the rest" |

Exact field formats: `common/messages.py`

## Layout
| Folder | Purpose |
|---|---|
| `common/` | message formats, network helpers, settings (ports, timeouts) |
| `controller/` | discovery, heartbeat, bully election, ordered multicast, reservation table |
| `agv/` | simulated vehicle |
| `viewer/` | optional display |
| `tests/` | tests |
| `docs/` | diagrams and notes |

## Who owns what
| Part | Files | Owner |
|---|---|---|
| Discovery | `controller/discovery.py` | |
| Leader election and heartbeat | `controller/election.py`, `controller/heartbeat.py` | |
| Ordered multicast | `controller/multicast.py` | |
| Fault tolerance, state, AGV | `controller/state.py`, `agv/` | |
| Shared message formats | `common/` | everyone, changes agreed in the group chat |

## Working rules
1. Never commit directly to `main`. Work on your own branch, then open a pull request.
2. At least one other member reads a pull request before it is merged.
3. Pull the latest `main` before you start work each day.
4. Only edit your own files unless you have agreed it in the group chat first.
5. Changes to `common/messages.py` affect everyone: announce them before merging.
6. Write short commit messages that say what changed.

## Requirements
- Python 3.x (version: TBD)
- Standard library only (no middleware)

## Running
Added as the parts come together. Planned:
```
python -m controller --id 1
python -m controller --id 2
python -m controller --id 3
python -m agv --id A1
```
When several nodes run on one machine, they must share the discovery port (`SO_REUSEADDR` / `SO_REUSEPORT`).

## Demo scenarios
1. Start 3 controllers and 2 AGVs; they find each other with no IPs configured.
2. Two AGVs request the same zone at the same moment; exactly one gets it, and every replica agrees.
3. Kill the leader; a new one is elected and existing reservations are kept.
4. Kill an AGV; its zones are released.
5. Restart a crashed controller; it catches up on the log before serving requests.