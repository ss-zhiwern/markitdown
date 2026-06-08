#!/usr/bin/env python3
"""Install/uninstall the markitdown-liberated ingest-guard hook in a Claude Code
settings.json, merging safely without disturbing other settings or hooks.

Usage:
  markitdown_hook_config.py install --command "<cmd>" [--settings PATH] [--matcher Read]
  markitdown_hook_config.py uninstall [--settings PATH]

Our hook entries are tagged with a marker so install is idempotent and uninstall
only removes what we added.
"""

import argparse
import json
import os
import sys

MARKER = "markitdown_ingest_guard"  # identifies our hook command


def default_settings_path() -> str:
    return os.path.join(os.path.expanduser("~"), ".claude", "settings.json")


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def is_ours(entry: dict) -> bool:
    for h in entry.get("hooks", []):
        if MARKER in (h.get("command") or ""):
            return True
    return False


def install(path: str, command: str, matcher: str) -> None:
    data = load(path)
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    # Drop any prior version of our entry, then append a fresh one.
    pre[:] = [e for e in pre if not is_ours(e)]
    pre.append(
        {
            "matcher": matcher,
            "hooks": [{"type": "command", "command": command}],
        }
    )
    save(path, data)
    print(f"[markitdown-liberated] ingest-guard hook installed in {path}")


def uninstall(path: str) -> None:
    data = load(path)
    pre = data.get("hooks", {}).get("PreToolUse")
    if not isinstance(pre, list):
        print(f"[markitdown-liberated] no hook found in {path}")
        return
    before = len(pre)
    pre[:] = [e for e in pre if not is_ours(e)]
    # Tidy empty containers.
    if not pre:
        data["hooks"].pop("PreToolUse", None)
    if not data.get("hooks"):
        data.pop("hooks", None)
    save(path, data)
    print(
        f"[markitdown-liberated] removed {before - len(pre)} ingest-guard hook(s) "
        f"from {path}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="action", required=True)

    p_in = sub.add_parser("install")
    p_in.add_argument("--command", required=True, help="full hook command string")
    p_in.add_argument("--settings", default=default_settings_path())
    p_in.add_argument("--matcher", default="Read")

    p_un = sub.add_parser("uninstall")
    p_un.add_argument("--settings", default=default_settings_path())

    args = ap.parse_args()
    if args.action == "install":
        install(args.settings, args.command, args.matcher)
    else:
        uninstall(args.settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
