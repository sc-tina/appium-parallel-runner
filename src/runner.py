"""Appium Parallel Test Runner."""
import argparse, json, logging, os, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
log = logging.getLogger(__name__)

class AppiumParallelRunner:
    def __init__(self, devices, apk_path=None):
        self.devices = devices
        self.results = {}

    def run_on_device(self, device):
        from appium import webdriver
        caps = {
            'platformName': 'Android', 'deviceName': device.get('name'),
            'udid': device.get('udid', ''), 'automationName': 'UiAutomator2',
            'noReset': device.get('no_reset', True), 'newCommandTimeout': 300,
        }
        if self.apk_path:
            caps['app'] = self.apk_path
        driver = None
        try:
            port = device.get('port', 4723)
            driver = webdriver.Remote(f'http://localhost:{port}/wd/hub', caps)
            log.info(f"{device['name']}: Session started")
            w, h = driver.get_window_size()['width'], driver.get_window_size()['height']
            driver.tap([(w//2, h//2)], 100)
            return {'device': device['name'], 'status': 'passed'}
        except Exception as e:
            return {'device': device['name'], 'status': 'error', 'error': str(e)}
        finally:
            if driver:
                try: driver.quit()
                except: pass

    def run_all(self):
        with ThreadPoolExecutor(max_workers=len(self.devices)) as ex:
            futures = {ex.submit(self.run_on_device, d): d for d in self.devices}
            return [f.result() for f in as_completed(futures)]

if __name__ == '__main__':
    import yaml
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    runner = AppiumParallelRunner(config.get('devices', []))
    print(json.dumps(runner.run_all(), indent=2))
