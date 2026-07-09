import urllib.request
import json
import sys

try:
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3) as r:
        data = json.loads(r.read().decode())
        print(f"SUCCESS: Backend health: {data}")
        sys.exit(0)
except Exception as e:
    print(f"FAILED: Could not connect to backend: {e}")
    sys.exit(1)
