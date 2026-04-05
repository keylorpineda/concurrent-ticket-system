import socket
import json

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9090


def send_request(request, host=DEFAULT_HOST, port=DEFAULT_PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(json.dumps(request).encode() + b"\n")
        data = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
    return json.loads(data.decode().strip())


def check(zone_id, host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_request({"action": "check", "zone_id": zone_id}, host, port)


def reserve(zone_id, row, col, host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_request({"action": "reserve", "zone_id": zone_id, "row": row, "col": col}, host, port)


def reserve_multiple(seats, host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_request({"action": "reserve_multiple", "seats": seats}, host, port)


def confirm(tx_id, host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_request({"action": "confirm", "tx_id": tx_id}, host, port)


def cancel(tx_id, host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_request({"action": "cancel", "tx_id": tx_id}, host, port)


def global_state(host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_request({"action": "global_state"}, host, port)


def get_log(host=DEFAULT_HOST, port=DEFAULT_PORT):
    return send_request({"action": "log"}, host, port)
