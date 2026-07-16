#!/usr/bin/env python3
"""Runtime and visual review for CampaignOS frontend modules.

The runner reuses a healthy CampaignOS server when one already exists. If the
configured URL is unavailable and points to localhost, it starts a temporary
static server and stops it after the review. When the default port is occupied
by an unhealthy process, the runner selects an available local port.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

BASE_URL = os.environ.get("CAMPAIGNOS_URL", "http://127.0.0.1:4173")
BASE_URL_EXPLICIT = "CAMPAIGNOS_URL" in os.environ
ARTIFACT_DIR = Path(os.environ.get("CAMPAIGNOS_ARTIFACT_DIR", "artifacts/campaignos-runtime"))
ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
SERVER_LOG = ARTIFACT_DIR / "server.log"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "[BLOCKED] Python Playwright is not installed in the active environment.\n"
            "Run:\n"
            "  python3 -m pip install -r scripts/frontend/requirements-runtime