<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Threading-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Threading" />
  <img src="https://img.shields.io/badge/Sockets_TCP-00599C?style=for-the-badge&logo=gnu&logoColor=white" alt="Sockets TCP" />
  <img src="https://img.shields.io/badge/Concurrency-FF6B6B?style=for-the-badge" alt="Concurrency" />
</div>

<h1 align="center">🎵 Concurrent System for Massive Concert Management</h1>

<p align="center">
  <strong>Phase II - Concurrent Implementation in a Local Environment</strong>
  <br />
  Client-server ticket reservation and sales system with explicit synchronization using threads, mutexes, and semaphores.
</p>

<p align="center">
  <strong>Course:</strong> EIF 212 Operating Systems &nbsp;|&nbsp;
  <strong>National University</strong> - Brunca Regional Campus
</p>

---

## 📖 Overview

The **Concurrent System for Massive Concert Management** simulates ticket sales for a concert divided into multiple zones (VIP, Preferred, and General). Each reservation or purchase request is handled by an independent thread, ensuring data integrity under high concurrency through explicit synchronization mechanisms.

The system implements a client-server architecture over TCP, where the server manages all shared resources and multiple clients connect simultaneously to check availability, make temporary reservations, and confirm purchases.

## ✨ Main Features

- **🔒 Explicit Mutual Exclusion:** `threading.Lock` per zone, reservation table, and event log - no frameworks that hide concurrency.
- **🚦 Counting Semaphores per Zone:** Real capacity control; decremented on reservation and incremented on cancellation or expiration.
- **⏱️ Automatic TTL:** Independent daemon thread that releases unconfirmed reservations within the time limit (30 seconds).
- **🔗 Hierarchical Lock Ordering:** Locks are always acquired in ascending zone order - formal deadlock prevention by eliminating circular wait (Coffman condition).
- **🛡️ Guaranteed Safety:** Seat state verification and update happen within the same critical section - double selling is impossible.
- **📡 TCP Architecture:** Socket-based communication, JSON protocol over TCP, one thread per client.
- **📋 Concurrent Global Event Log:** Event logging protected with an independent lock.
- **🧪 Load Generator:** Testing module that simulates conflict and high-load scenarios with result tracking.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.8+ |
| Concurrency | `threading` (Lock, Semaphore, Thread) |
| Communication | `socket` - TCP/IP |
| Serialization | `json` (message protocol) |
| Identifiers | `uuid` |

> All concurrency is implemented using Python's standard library, without third-party frameworks, meeting the project's explicit requirement.

## 📂 Project Architecture

```text
concierto/
 ├── shared/
 │    ├── recursos.py       # Core system: ConcertSystem, seat matrix,
 │    │                     # semaphores, locks, reservation table, and event log
 │    └── gestor_ttl.py     # TTLManager: daemon thread that processes expirations
 │
 ├── server/
 │    └── servidor.py       # Concurrent TCP server - one thread per client
 │
 └── client/
      ├── cliente_lib.py          # Communication library (send_request and helpers)
      ├── cliente_interactivo.py  # TUI menu for manual use
      └── prueba_concurrente.py   # Load generator and concurrency tests
```

## 🔧 Shared Resources and Synchronization Mechanisms

| Resource | Mechanism | Description |
|---|---|---|
| `seat_matrix[zone][row][col]` | `zone_lock[i]` (Lock) | Three-dimensional seat matrix - main critical section |
| Semaphore per zone | `threading.Semaphore(capacity)` | Controls availability; blocks threads when the zone is full |
| `reservations` (table) | `table_lock` (Lock) | Dictionary of active transactions with TTL |
| `event_log` (log) | `log_lock` (Lock) | Chronological record of all system events |
| TTL manager | `threading.Thread(daemon=True)` | Background thread that checks and releases expired reservations every 5 seconds |

## 🚀 How to Run

### Prerequisites

- Python 3.8 or superior
- No external dependencies - standard library only

### Installation

```bash
git clone https://github.com/tu-usuario/concierto-so.git
cd concierto-so
```

### Start the Server

```bash
python server/servidor.py
```

The server listens on `0.0.0.0:9090` and creates one thread for each connected client.

### Start the Interactive Client

```bash
python client/cliente_interactivo.py
```

Console menu with the following options:

```
1. Check availability by zone
2. Reserve seat
3. Reserve multiple seats
4. Confirm purchase
5. Cancel reservation
6. Global system status
7. View event log
```

### Run Concurrency Tests

```bash
python client/prueba_concurrente.py
```

Runs two automatic scenarios:
- **Conflict Scenario:** 10 users competing for the same seat simultaneously.
- **Load Scenario:** 30 users reserving random seats in parallel.

Results are saved in `logs_prueba_concurrente.txt`.

## 🔄 Protected Reservation Flow

```
Client sends request
        │
        ▼
semaphore[zone].acquire()  ← blocks if zone is full
        │
        ▼
zone_lock[i].acquire()     ← mutual exclusion over the matrix
        │
        ▼
Check seat status
        │
   ┌────┴────┐
   │         │
AVAILABLE   NOT AVAILABLE → release semaphore → error
   │
   ▼
Mark as RESERVED
        │
        ▼
table_lock.acquire()       ← protect reservation table
        │
        ▼
Insert transaction (tx_id, timestamp, TTL)
        │
        ▼
Release locks in reverse order
        │
        ▼
log_lock → record event → Reservation successful ✓
```

## 🧵 Deadlock Prevention

The **circular wait condition** (Coffman) is removed by enforcing a mandatory global hierarchical lock acquisition order:

```
Level 1: semaphores[zone_id]   → always in ascending index order
Level 2: zone_lock[zone_id]    → always in ascending index order
Level 3: table_lock
Level 4: log_lock
```

No thread may acquire a lower-level lock after already acquiring a higher-level one. Locks are always released in reverse order inside `try/finally` blocks.

## 📊 Correctness Properties

| Property | Guarantee |
|---|---|
| **Safety** | No seat can be confirmed for two clients simultaneously - verification and marking occur in the same critical section |
| **Liveness** | `try/finally` guarantees lock release; hierarchical ordering eliminates deadlocks; TTL daemon prevents indefinite blocking |

## 📄 License

This project is for academic use under the guidelines of the EIF 212 Operating Systems course, National University of Costa Rica.
