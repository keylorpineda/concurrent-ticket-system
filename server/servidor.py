import socket
import threading
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.recursos import ConcertSystem, ZONE_CONFIG
from shared.gestor_ttl import TTLManager

HOST = "0.0.0.0"
PORT = 9090


def handle_client(conn, addr, system):
    try:
        with conn:
            data = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\n" in data:
                    break
            if not data:
                return
            try:
                request = json.loads(data.decode().strip())
            except json.JSONDecodeError:
                conn.sendall(json.dumps({"ok": False, "error": "JSON inválido"}).encode() + b"\n")
                return
            response = process_request(request, system)
            conn.sendall(json.dumps(response).encode() + b"\n")
    except Exception as e:
        try:
            conn.sendall(json.dumps({"ok": False, "error": str(e)}).encode() + b"\n")
        except Exception:
            pass


def process_request(request, system):
    action = request.get("action", "")

    if action == "check":
        zone_id = request.get("zone_id")
        state, err = system.check_availability(zone_id)
        if err:
            return {"ok": False, "error": err}
        return {"ok": True, "state": state}

    elif action == "reserve":
        zone_id = request.get("zone_id")
        row     = request.get("row")
        col     = request.get("col")
        tx_id, err = system.reserve_seat(zone_id, row, col)
        if err:
            return {"ok": False, "error": err}
        return {"ok": True, "tx_id": tx_id}

    elif action == "reserve_multiple":
        requests = [tuple(s) for s in request.get("seats", [])]
        tx_id, err = system.reserve_multiple(requests)
        if err:
            return {"ok": False, "error": err}
        return {"ok": True, "tx_id": tx_id}

    elif action == "confirm":
        tx_id   = request.get("tx_id")
        ok, err = system.confirm_purchase(tx_id)
        if err:
            return {"ok": False, "error": err}
        return {"ok": True}

    elif action == "cancel":
        tx_id   = request.get("tx_id")
        ok, err = system.cancel_reservation(tx_id)
        if err:
            return {"ok": False, "error": err}
        return {"ok": True}

    elif action == "global_state":
        return {"ok": True, "state": system.get_global_state()}

    elif action == "log":
        return {"ok": True, "log": system.get_log()}

    else:
        return {"ok": False, "error": f"Acción desconocida: {action}"}


def start_server():
    system      = ConcertSystem()
    ttl_manager = TTLManager(system)
    ttl_manager.start()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(128)

    print(f"Servidor iniciado en {HOST}:{PORT}")
    print(f"Zonas disponibles: {', '.join(v['nombre'] for v in ZONE_CONFIG.values())}")
    print("Esperando conexiones...\n")

    try:
        while True:
            conn, addr = srv.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, system),
                daemon=True
            )
            thread.start()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        srv.close()
        ttl_manager.stop()


if __name__ == "__main__":
    start_server()
