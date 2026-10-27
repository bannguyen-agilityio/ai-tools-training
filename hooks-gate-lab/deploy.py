"""Fake deploy script. It only prints - safe to run.

Usage: python3 deploy.py staging | production
"""
import sys
import time

env = sys.argv[1] if len(sys.argv) > 1 else "staging"
print(f"(pretend) deploying app to {env} ...")
time.sleep(1)
print(f"done: {env}")
