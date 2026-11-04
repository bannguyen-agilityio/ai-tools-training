"""Lesson 2: Getting an API key. Put ANTHROPIC_API_KEY in .env (never commit it)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
key = os.environ.get("ANTHROPIC_API_KEY")
if not key:
    raise SystemExit(
        "ANTHROPIC_API_KEY missing. "
        "Create one at https://console.anthropic.com and add it to .env"
    )
print(f"Key loaded: {key[:10]}...{key[-4:]}")
