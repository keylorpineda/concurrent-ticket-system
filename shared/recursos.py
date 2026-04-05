import threading
import time
import uuid

ZONE_CONFIG = {
    0: {"nombre": "VIP",          "rows": 5,  "cols": 8},
    1: {"nombre": "Preferencial", "rows": 8,  "cols": 12},
    2: {"nombre": "General",      "rows": 10, "cols": 15},
}

AVAILABLE = "D"
RESERVED  = "R"
SOLD      = "V"

TTL_SECONDS = 30


class ConcertSystem:
    def __init__(self):
        self.seat_matrix  = {}
        self.semaphores   = {}
        self.zone_lock    = {}
        self.table_lock   = threading.Lock()
        self.log_lock     = threading.Lock()
        self.reservations = {}
        self.event_log    = []

        for zone_id, cfg in ZONE_CONFIG.items():
            capacity = cfg["rows"] * cfg["cols"]
            self.semaphores[zone_id]  = threading.Semaphore(capacity)
            self.zone_lock[zone_id]   = threading.Lock()
            self.seat_matrix[zone_id] = [
                [AVAILABLE] * cfg["cols"] for _ in range(cfg["rows"])
            ]

    def _log(self, message):
        ts    = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {message}"
        with self.log_lock:
            self.event_log.append(entry)
            print(entry)

    def check_availability(self, zone_id):
        if zone_id not in self.seat_matrix:
            return None, "Zona no existe"
        with self.zone_lock[zone_id]:
            snapshot = [row[:] for row in self.seat_matrix[zone_id]]
        return snapshot, None

    def reserve_seat(self, zone_id, row, col):
        if zone_id not in self.seat_matrix:
            return None, "Zona no existe"
        cfg = ZONE_CONFIG[zone_id]
        if row < 0 or row >= cfg["rows"] or col < 0 or col >= cfg["cols"]:
            return None, "Asiento fuera de rango"

        acquired = self.semaphores[zone_id].acquire(timeout=5)
        if not acquired:
            return None, "Sin disponibilidad en la zona"

        try:
            with self.zone_lock[zone_id]:
                if self.seat_matrix[zone_id][row][col] != AVAILABLE:
                    self.semaphores[zone_id].release()
                    return None, "Asiento no disponible"
                self.seat_matrix[zone_id][row][col] = RESERVED

            tx_id = str(uuid.uuid4())[:8].upper()
            with self.table_lock:
                self.reservations[tx_id] = {
                    "zone_id": zone_id,
                    "seats":   [(row, col)],
                    "created": time.time(),
                    "ttl":     TTL_SECONDS,
                    "active":  True,
                }
            self._log(f"RESERVA {tx_id} | Zona {ZONE_CONFIG[zone_id]['nombre']} F{row}C{col}")
            return tx_id, None

        except Exception as e:
            self.semaphores[zone_id].release()
            return None, str(e)

    def reserve_multiple(self, requests):
        unique_zones = sorted(set(r[0] for r in requests))

        for zone_id in unique_zones:
            if not self.semaphores[zone_id].acquire(timeout=5):
                for z in unique_zones[:unique_zones.index(zone_id)]:
                    self.semaphores[z].release()
                return None, f"Sin disponibilidad en zona {zone_id}"

        acquired_locks = []
        try:
            for zone_id in unique_zones:
                self.zone_lock[zone_id].acquire()
                acquired_locks.append(zone_id)

            for zone_id, row, col in requests:
                cfg = ZONE_CONFIG[zone_id]
                if row < 0 or row >= cfg["rows"] or col < 0 or col >= cfg["cols"]:
                    raise ValueError(f"Asiento fuera de rango: Z{zone_id} F{row}C{col}")
                if self.seat_matrix[zone_id][row][col] != AVAILABLE:
                    raise ValueError(f"Asiento no disponible: Z{zone_id} F{row}C{col}")

            for zone_id, row, col in requests:
                self.seat_matrix[zone_id][row][col] = RESERVED

        except ValueError as e:
            for zone_id, row, col in requests:
                if self.seat_matrix[zone_id][row][col] == RESERVED:
                    self.seat_matrix[zone_id][row][col] = AVAILABLE
            for z in acquired_locks:
                self.zone_lock[z].release()
            for z in unique_zones:
                self.semaphores[z].release()
            return None, str(e)

        tx_id = str(uuid.uuid4())[:8].upper()
        with self.table_lock:
            self.reservations[tx_id] = {
                "zone_id":  requests[0][0],
                "seats":    [(z, r, c) for z, r, c in requests],
                "created":  time.time(),
                "ttl":      TTL_SECONDS,
                "active":   True,
                "multiple": True,
            }

        for z in acquired_locks:
            self.zone_lock[z].release()

        self._log(f"RESERVA MULTIPLE {tx_id} | {len(requests)} asientos en zonas {unique_zones}")
        return tx_id, None

    def confirm_purchase(self, tx_id):
        with self.table_lock:
            res = self.reservations.get(tx_id)
            if not res or not res["active"]:
                return False, "Transacción no válida o ya procesada"
            res["active"] = False

        multiple = res.get("multiple", False)
        seats    = res["seats"]

        if multiple:
            for z in sorted(set(s[0] for s in seats)):
                with self.zone_lock[z]:
                    for s in seats:
                        if s[0] == z:
                            self.seat_matrix[s[0]][s[1]][s[2]] = SOLD
        else:
            row, col = seats[0]
            with self.zone_lock[res["zone_id"]]:
                self.seat_matrix[res["zone_id"]][row][col] = SOLD

        self._log(f"COMPRA CONFIRMADA {tx_id}")
        return True, None

    def cancel_reservation(self, tx_id):
        with self.table_lock:
            res = self.reservations.get(tx_id)
            if not res or not res["active"]:
                return False, "Transacción no válida o ya procesada"
            res["active"] = False

        self._release_seats(res)
        self._log(f"CANCELACION {tx_id}")
        return True, None

    def _release_seats(self, reservation):
        seats    = reservation["seats"]
        multiple = reservation.get("multiple", False)

        if multiple:
            for z in sorted(set(s[0] for s in seats)):
                with self.zone_lock[z]:
                    for s in seats:
                        if s[0] == z:
                            self.seat_matrix[s[0]][s[1]][s[2]] = AVAILABLE
                self.semaphores[z].release()
        else:
            row, col = seats[0]
            zone_id  = reservation["zone_id"]
            with self.zone_lock[zone_id]:
                self.seat_matrix[zone_id][row][col] = AVAILABLE
            self.semaphores[zone_id].release()

    def process_expirations(self):
        now     = time.time()
        expired = []
        with self.table_lock:
            for tx_id, res in self.reservations.items():
                if res["active"] and (now - res["created"]) > res["ttl"]:
                    res["active"] = False
                    expired.append((tx_id, dict(res)))
        for tx_id, res in expired:
            self._release_seats(res)
            self._log(f"TTL EXPIRADO {tx_id}")

    def get_log(self):
        with self.log_lock:
            return list(self.event_log)

    def get_global_state(self):
        state = {}
        for zone_id, cfg in ZONE_CONFIG.items():
            with self.zone_lock[zone_id]:
                matrix_copy = [row[:] for row in self.seat_matrix[zone_id]]
            total     = cfg["rows"] * cfg["cols"]
            sold      = sum(r.count(SOLD)     for r in matrix_copy)
            reserved  = sum(r.count(RESERVED) for r in matrix_copy)
            available = total - sold - reserved
            state[zone_id] = {
                "nombre":      cfg["nombre"],
                "total":       total,
                "disponibles": available,
                "reservados":  reserved,
                "vendidos":    sold,
                "matrix":      matrix_copy,
            }
        return state
