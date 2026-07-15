# Appium Parallel Runner

Run Appium tests on multiple Android devices simultaneously. Device pool management, parallel execution, and HTML/JSON test reports.

## Features
- Parallel test execution across multiple Android devices
- Auto-discovery of ADB-connected devices
- Thread-safe device pool with health monitoring
- Rich HTML/JSON test reports
- Docker Compose setup for Appium server nodes

## Quick Start

```bash
pip install -r requirements.txt
python -c "from src.pool import DevicePool; print('DevicePool ready')"
python src/runner.py --config config.yaml
```

## Contact
- Website: https://www.qtphone.com/
- WhatsApp: @along915
- Telegram: @Alongyun
