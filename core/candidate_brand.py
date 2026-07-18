#!/usr/bin/env python3
"""Deterministic, read-only Candidate Brand and Reputation aggregate."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from typing import Any

SCHEMA_VERSION = "1.0"
SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
PERSONAL_PATH = re.compile(r"(?:/Users/[^/]+|/home/[^/]+|[A-Za-z]:\\\\Users\\\\[^\\\\]+)")
EVIDENCE_CLASSES =