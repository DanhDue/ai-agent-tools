#!/usr/bin/env python3
"""
clean_antigravity_cache.py
Safely purges disposable caches, stale V8 bytecode, Chromium webview caches,
and orphaned installers across Antigravity profiles to recover disk space.

Zero impact on:
- Account authentication & macOS Keychain tokens
- Extension installations & settings.json
- Active conversations & brain transcripts
- Machine IDs & profile isolation
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import sys
import time

# Terminal ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
DIM = "\033[2m"

RESERVED_NON_PROFILES = {
    "Library", "System", "Shared", "AllProjects", "Projects", "fvm",
    "claude", "codex", "kiro", "anthropic", "openai", ".gemini", ".antigravity",
    ".antigravity-ide"
}


def get_default_homes_dir() -> str:
    current_home = os.path.expanduser("~")
    real_home = current_home.split("/antigravity_homes")[0] if "antigravity_homes" in current_home else current_home
    return f"{real_home}/antigravity_homes"


def is_valid_profile_dir(path: str) -> bool:
    if not os.path.exists(path) or os.path.islink(path):
        return False
    if not os.path.isdir(path):
        return False

    name = os.path.basename(path)
    if name.startswith(".") or name.startswith("-") or name in RESERVED_NON_PROFILES:
        return False
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        return False

    has_gemini = os.path.exists(os.path.join(path, ".gemini"))
    has_ag = os.path.exists(os.path.join(path, ".antigravity"))
    has_data = os.path.exists(os.path.join(path, "data"))
    has_kc = os.path.exists(os.path.join(path, "Library/Keychains"))
    return bool(has_gemini or has_ag or has_data or has_kc)


def get_dir_size(path: str) -> int:
    """Calculate directory size in bytes without traversing symlinks."""
    total = 0
    if not os.path.exists(path) or os.path.islink(path):
        return 0
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                if not os.path.islink(fp) and os.path.exists(fp):
                    try:
                        total += os.path.getsize(fp)
                    except OSError:
                        pass
    except OSError:
        pass
    return total


def clean_profile_cache(p_path: str, profile_name: str, dry_run: bool = False) -> dict:
    """Cleans disposable cache items from a single Antigravity profile."""
    stats = {
        "profile": profile_name,
        "docker_install_bytes": 0,
        "cached_data_bytes": 0,
        "cached_vsix_bytes": 0,
        "data_cache_bytes": 0,
        "webview_cache_storage_bytes": 0,
        "old_bak_bytes": 0,
        "total_bytes": 0,
    }

    # 1. Purge com.docker.install junk directory (if exists)
    docker_dir = os.path.join(p_path, "Library/Application Support/com.docker.install")
    if os.path.exists(docker_dir) and not os.path.islink(docker_dir):
        sz = get_dir_size(docker_dir)
        stats["docker_install_bytes"] += sz
        if not dry_run:
            try:
                shutil.rmtree(docker_dir, ignore_errors=True)
            except Exception:
                pass

    # 2. Purge CachedData (V8 Bytecode cache)
    cached_data_dir = os.path.join(p_path, "data/CachedData")
    if os.path.exists(cached_data_dir) and not os.path.islink(cached_data_dir):
        sz = get_dir_size(cached_data_dir)
        stats["cached_data_bytes"] += sz
        if not dry_run:
            try:
                shutil.rmtree(cached_data_dir, ignore_errors=True)
            except Exception:
                pass

    # 3. Purge CachedExtensionVSIXs (Stale extension installers)
    vsix_dir = os.path.join(p_path, "data/CachedExtensionVSIXs")
    if os.path.exists(vsix_dir) and not os.path.islink(vsix_dir):
        sz = get_dir_size(vsix_dir)
        stats["cached_vsix_bytes"] += sz
        if not dry_run:
            try:
                shutil.rmtree(vsix_dir, ignore_errors=True)
            except Exception:
                pass

    # 4. Purge data/Cache (Chromium HTTP/disk cache)
    cache_dir = os.path.join(p_path, "data/Cache")
    if os.path.exists(cache_dir) and not os.path.islink(cache_dir):
        sz = get_dir_size(cache_dir)
        stats["data_cache_bytes"] += sz
        if not dry_run:
            try:
                shutil.rmtree(cache_dir, ignore_errors=True)
            except Exception:
                pass

    # 5. Purge WebStorage CacheStorage (Webview Service Worker / HTTP cache)
    web_storage_dir = os.path.join(p_path, "data/WebStorage")
    if os.path.exists(web_storage_dir) and not os.path.islink(web_storage_dir):
        for root, dirs, _ in os.walk(web_storage_dir):
            if "CacheStorage" in dirs:
                cs_path = os.path.join(root, "CacheStorage")
                if not os.path.islink(cs_path):
                    sz = get_dir_size(cs_path)
                    stats["webview_cache_storage_bytes"] += sz
                    if not dry_run:
                        try:
                            shutil.rmtree(cs_path, ignore_errors=True)
                        except Exception:
                            pass

    # 6. Purge redundant .bak.* files older than 24 hours
    now = time.time()
    for root, dirs, files in os.walk(p_path):
        # Do not descend into symlinked toolchains
        if os.path.islink(root):
            continue
        for f in files:
            if ".bak." in f:
                fp = os.path.join(root, f)
                if not os.path.islink(fp) and os.path.exists(fp):
                    try:
                        mtime = os.path.getmtime(fp)
                        # Remove if older than 24 hours (86400s)
                        if (now - mtime) > 86400:
                            sz = os.path.getsize(fp)
                            stats["old_bak_bytes"] += sz
                            if not dry_run:
                                os.remove(fp)
                    except OSError:
                        pass

    stats["total_bytes"] = (
        stats["docker_install_bytes"]
        + stats["cached_data_bytes"]
        + stats["cached_vsix_bytes"]
        + stats["data_cache_bytes"]
        + stats["webview_cache_storage_bytes"]
        + stats["old_bak_bytes"]
    )
    return stats


def clean_all_profiles(homes_dir: str | None = None, target: str | None = None, dry_run: bool = False) -> list[dict]:
    if not homes_dir:
        homes_dir = get_default_homes_dir()

    profile_paths = sorted(glob.glob(f"{homes_dir}/*"))
    profiles = [p for p in profile_paths if is_valid_profile_dir(p)]

    if target:
        profiles = [p for p in profiles if os.path.basename(p) == target]

    results = []
    for p_path in profiles:
        p_name = os.path.basename(p_path)
        res = clean_profile_cache(p_path, p_name, dry_run=dry_run)
        results.append(res)
    return results


def format_bytes(n: int) -> str:
    if n >= 1024 ** 3:
        return f"{n / (1024 ** 3):.2f} GB"
    if n >= 1024 ** 2:
        return f"{n / (1024 ** 2):.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def print_clean_report(results: list[dict], dry_run: bool = False):
    action = "SIMULATION (DRY-RUN)" if dry_run else "CLEANUP COMPLETE"
    color = YELLOW if dry_run else GREEN

    print(f"\n{BOLD}{color}╔══════════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{color}║                    ANTIGRAVITY PROFILE DISK OPTIMIZATION: {action:<30} ║{RESET}")
    print(f"{BOLD}{color}╚══════════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

    header = f"{'PROFILE':<20} | {'V8 BYTECODE':<13} | {'WEBVIEW CACHE':<14} | {'HTTP CACHE':<12} | {'TOTAL RECLAIMED'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * 80)

    grand_total = 0
    total_docker = 0
    total_v8 = 0
    total_vsix = 0
    total_http = 0
    total_webview = 0
    total_baks = 0

    for r in results:
        tot = r["total_bytes"]
        grand_total += tot
        total_docker += r["docker_install_bytes"]
        total_v8 += r["cached_data_bytes"]
        total_vsix += r["cached_vsix_bytes"]
        total_http += r["data_cache_bytes"]
        total_webview += r["webview_cache_storage_bytes"]
        total_baks += r["old_bak_bytes"]

        if tot > 0:
            v8_str = format_bytes(r["cached_data_bytes"])
            wv_str = format_bytes(r["webview_cache_storage_bytes"])
            http_str = format_bytes(r["data_cache_bytes"])
            tot_str = f"{BOLD}{GREEN}{format_bytes(tot)}{RESET}"
            print(f"{r['profile']:<20} | {v8_str:<13} | {wv_str:<14} | {http_str:<12} | {tot_str}")

    print("-" * 80)
    print(f"{BOLD}Summary of Reclaimed Space:{RESET}")
    if total_docker > 0:
        print(f"  • {CYAN}Orphaned Docker Installer{RESET} : {format_bytes(total_docker)}")
    print(f"  • {CYAN}Webview CacheStorage{RESET}      : {format_bytes(total_webview)}")
    print(f"  • {CYAN}V8 Bytecode (CachedData){RESET}   : {format_bytes(total_v8)}")
    print(f"  • {CYAN}Chromium HTTP Cache{RESET}        : {format_bytes(total_http)}")
    print(f"  • {CYAN}Stale Extension VSIXs{RESET}      : {format_bytes(total_vsix)}")
    print(f"  • {CYAN}Old Backup Files (>24h){RESET}    : {format_bytes(total_baks)}")
    print(f"\n{BOLD}{GREEN}✓ TOTAL SPACE {'RECLAIMABLE' if dry_run else 'RECLAIMED'}: {format_bytes(grand_total)}{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="Clean Antigravity Profile Caches & Recover Disk Space")
    parser.add_argument("--dry-run", action="store_true", help="Preview reclaimable space without deleting files")
    parser.add_argument("--target", type=str, default=None, help="Target a specific profile")
    parser.add_argument("--homes-dir", type=str, default=None, help="Custom antigravity_homes directory")

    args = parser.parse_args()

    results = clean_all_profiles(args.homes_dir, args.target, dry_run=args.dry_run)
    print_clean_report(results, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())

