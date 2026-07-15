"""Device pool manager."""
import logging, subprocess, threading, time

log = logging.getLogger(__name__)

class DevicePool:
    def __init__(self):
        self._devices = {}
        self._lock = threading.Lock()

    def register(self, udid, name='', port=4723):
        with self._lock:
            self._devices[udid] = {'udid': udid, 'name': name, 'port': port, 'status': 'available'}

    def acquire(self):
        with self._lock:
            for uid, info in self._devices.items():
                if info['status'] == 'available':
                    info['status'] = 'busy'
                    return info
        return None

    def release(self, udid):
        with self._lock:
            if udid in self._devices:
                self._devices[udid]['status'] = 'available'

    def health_check(self, udid):
        try:
            r = subprocess.run(['adb', '-s', udid, 'get-state'], capture_output=True, text=True, timeout=5)
            return r.returncode == 0 and 'device' in r.stdout
        except:
            return False
