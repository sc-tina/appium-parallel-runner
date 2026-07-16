#!/usr/bin/env python3
"""Appium Parallel Test Runner - optimized."""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DeviceConfig:
    name: str
    udid: str
    port: int = 4723
    no_reset: bool = True
    app_path: Optional[str] = None


@dataclass
class TestResult:
    device: str
    status: str
    message: str = ""
    error: Optional[str] = None
    elapsed: float = 0.0


class AppiumParallelRunner:
    """Run Appium tests across multiple Android devices in parallel."""

    def __init__(
        self,
        devices: list[dict],
        apk_path: Optional[str] = None,
        max_workers: int = 10,
    ) -> None:
        self.devices = [
            DeviceConfig(
                name=d.get("name", d.get("udid", "unknown")),
                udid=d.get("udid", ""),
                port=d.get("port", 4723),
                no_reset=d.get("no_reset", True),
                app_path=d.get("app_path"),
            )
            for d in devices
        ]
        self.apk_path = apk_path  # BUGFIX: actually store it
        self.max_workers = max_workers
        self.results = {}
        self._lock = threading.Lock()

    def _build_caps(self, device: DeviceConfig) -> dict:
        caps = {
            "platformName": "Android",
            "deviceName": device.name,
            "udid": device.udid,
            "automationName": "UiAutomator2",
            "noReset": device.no_reset,
            "newCommandTimeout": 300,
        }
        app = device.app_path or self.apk_path
        if app:
            caps["app"] = app
        return caps

    def run_on_device(self, device: DeviceConfig) -> TestResult:
        start = time.time()
        driver = None
        try:
            from appium import webdriver
            caps = self._build_caps(device)
            hub_url = f"http://localhost:{device.port}/wd/hub"
            logger.info("Connecting to %s at %s", device.name, hub_url)
            driver = webdriver.Remote(hub_url, caps)
            w = driver.get_window_size()["width"]
            h = driver.get_window_size()["height"]
            driver.tap([(w // 2, h // 2)], 100)
            elapsed = time.time() - start
            logger.info("%s: PASSED (%.2fs)", device.name, elapsed)
            return TestResult(device=device.name, status="passed", elapsed=elapsed)
        except ImportError:
            msg = "appium package not installed"
            logger.error("%s: %s", device.name, msg)
            return TestResult(device=device.name, status="error", message=msg)
        except Exception as e:
            elapsed = time.time() - start
            logger.error("%s: ERROR %s (%.2fs)", device.name, e, elapsed)
            return TestResult(device=device.name, status="error", error=str(e), elapsed=elapsed)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.warning("Failed to quit driver for %s: %s", device.name, e)

    def run_all(self) -> list[dict]:
        if not self.devices:
            logger.warning("No devices configured")
            return []
        workers = min(self.max_workers, len(self.devices))
        logger.info("Starting run on %d device(s)", len(self.devices))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(self.run_on_device, d): d for d in self.devices}
            for f in as_completed(futures):
                r = f.result()
                with self._lock:
                    self.results[r.device] = r
        return [
            {"device": r.device, "status": r.status, "message": r.message,
             "error": r.error, "elapsed": round(r.elapsed, 3)}
            for r in sorted(self.results.values(), key=lambda x: x.device)
        ]


def load_config(path: str) -> list:
    import yaml
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data.get("devices", [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Appium Parallel Test Runner")
    parser.add_argument("-c", "--config", default="config.yaml")
    parser.add_argument("-a", "--apk")
    parser.add_argument("-j", "--json", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    try:
        devices = load_config(args.config)
    except FileNotFoundError:
        logger.error("Config not found: %s", args.config)
        sys.exit(1)
    except Exception as e:
        logger.error("Config load error: %s", e)
        sys.exit(1)

    results = AppiumParallelRunner(devices, apk_path=args.apk_path).run_all()
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        passed = sum(1 for r in results if r["status"] == "passed")
        failed = sum(1 for r in results if r["status"] == "error")
        print(f"\nResults: {passed} passed, {failed} failed / {len(results)} total")
        for r in results:
            icon = "PASS" if r["status"] == "passed" else "FAIL"
            extra = f" ({r.get('error','')})" if r.get("error") else ""
            print(f"  [{icon}] {r['device']}{extra}")


if __name__ == "__main__":
    main()
