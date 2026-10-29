"""Public website checks: every named comparison has results, links and anchors resolve, no reader link opens Markdown."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SiteTest(unittest.TestCase):
    def test_site_validates(self):
        r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "build_site.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS site", r.stdout)


if __name__ == "__main__":
    unittest.main()
