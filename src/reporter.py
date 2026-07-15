"""Test report generator."""
import json, os, time

class TestReporter:
    def __init__(self, output_dir='reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_json(self, results):
        report = {
            'timestamp': time.time(),
            'summary': {
                'total': len(results),
                'passed': sum(1 for r in results if r.get('status') == 'passed'),
                'failed': sum(1 for r in results if r.get('status') == 'failed'),
                'error': sum(1 for r in results if r.get('status') == 'error'),
            },
            'results': results
        }
        path = os.path.join(self.output_dir, 'report.json')
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        return path
