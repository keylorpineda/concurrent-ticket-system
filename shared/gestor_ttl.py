import threading
import time


class TTLManager(threading.Thread):
    def __init__(self, system, interval=5):
        super().__init__(daemon=True)
        self.system   = system
        self.interval = interval
        self._running = True

    def run(self):
        while self._running:
            time.sleep(self.interval)
            self.system.process_expirations()

    def stop(self):
        self._running = False
