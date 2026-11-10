# AGV

Distributed traffic control for simulated Automated Guided Vehicles (AGVs).
Controller nodes keep a replicated reservation table of warehouse zones. AGVs
must reserve a zone before entering it. Course project, Distributed Systems, WS 2026/27.

## Architecture (hybrid)
- Client-server between AGVs and controllers
- Peer-to-peer among the controller nodes, with one leader chosen by the bully algorithm

## Layout
| Folder | Purpose |
|---|---|
| `common/` | message formats, network helpers, settings |
| `controller/` | discovery, heartbeat, bully election, ordered multicast, reservation table |
| `agv/` | simulated vehicle |
| `viewer/` | optional display |
| `tests/` | tests |
| `docs/` | diagrams and notes |

## Who owns what
| Part | Owner |
|---|---|
| Discovery (`controller/discovery.py`) | |
| Leader election and heartbeat (`election.py`, `heartbeat.py`) | |
| Ordered multicast (`multicast.py`) | |
| Fault tolerance, state, AGV (`state.py`, `agv/`) | |

## Working rules
1. Never commit directly to `main`. Work on your own branch, then open a pull request.
2. At least one other member reads a pull request before it is merged.
3. Pull the latest `main` before you start work each day.
4. Only edit your own files unless you have agreed it in the group chat first.
5. Write short commit messages that say what changed.

## Running
Added as the parts come together.
