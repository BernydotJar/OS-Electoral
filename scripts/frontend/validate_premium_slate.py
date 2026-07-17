#!/usr/bin/env python3
"""Static contract validation for C1-FRONT-004 Premium Slate."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "web" / "index.html"
CSS = ROOT / "web" / "premium-slate.css"
JS = ROOT / "web" / "premium-slate.js"
REQUIREMENTS = ROOT / "specs" / "C1-FRONT-004" / "requirements.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    for path in (INDEX, CSS, JS, REQUIREMENTS):
        require(path.is_file(), f"missing required file: {path.relative_to(ROOT)}")

    index = INDEX.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    combined = "\n".join((index, css, js)).lower()

    require('<link rel="stylesheet" href="./premium-slate.css">' in index, "premium stylesheet is not linked")
    require('<script src="./premium-slate.js" defer></script>' in index, "premium runtime is not loaded with defer")
    require(
        re.search(r'<canvas\s+id="ambientCanvas"\s+aria-hidden="true"', index) is not None,
        "ambient canvas must be decorative and aria-hidden",
    )
    require('data-active-module="team"' in index, "initial module state metadata is missing")
    require('id="activeModuleStatus"' in index, "module coordinate status is missing")

    required_tokens = (
        "--canvas:",
        "--surface-1:",
        "--surface-border:",
        "--accent-h:",
        "--approval:",
        "--warning:",
        "--danger:",
        "--focus:",
    )
    for token in required_tokens:
        require(token in css, f"missing premium token: {token}")

    require("background-size: 20px 20px" in css, "20px dotted grid contract is missing")
    require("#ambientCanvas" in css and "pointer-events: none" in css, "ambient canvas must not intercept input")
    require(".premium-glow::after" in css, "glow primitive is missing")
    require("::view-transition-new(root)" in css, "View Transition styling is missing")
    require("clip-path: circle" in css, "circular reveal contract is missing")
    require("@media (prefers-reduced-motion: reduce)" in css, "reduced-motion CSS fallback is missing")
    require("@media (pointer: coarse)" in css, "coarse-pointer glow fallback is missing")

    require('getcontext("2d", { alpha: true })' in js.lower(), "ambient canvas must use a 2D alpha context")
    require("Math.min(window.devicePixelRatio || 1, 2)" in js, "canvas DPR cap is missing")
    require("document.hidden" in js, "canvas visibility pause is missing")
    require("prefers-reduced-motion: reduce" in js, "runtime reduced-motion detection is missing")
    require("pointer: coarse" in js, "runtime coarse-pointer detection is missing")
    require("MutationObserver" in js, "dynamic cards are not hydrated")
    require("body.dataset.activeModule" in js, "active module metadata synchronization is missing")

    forbidden_terms = (
        "sendmessage(",
        "publishto",
        "adspend",
        "voterscore",
        "persuasionscore",
        "mobilizevoter",
        "citizenprofile",
    )
    for term in forbidden_terms:
        require(term not in combined, f"forbidden capability marker found: {term}")

    require(index.count('id="ambientCanvas"') == 1, "ambient canvas ID must be unique")
    require(index.count('id="activeModuleStatus"') == 1, "active module status ID must be unique")

    print("[OK] premium slate assets and shell integration")
    print("[OK] decorative canvas is aria-hidden and non-interactive")
    print("[OK] glow, circular reveal and reduced-motion contracts")
    print("[OK] no forbidden political execution capability markers")


if __name__ == "__main__":
    main()
