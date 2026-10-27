"""Explicit offline native-plugin check; uses the configured VM, never starts model inference."""
from tools.native_check import run

if __name__ == '__main__':
    raise SystemExit(0 if run()['passed'] else 1)
