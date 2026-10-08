"""Dual-mode in-place self-updater for AutoLaunch.

Supports both Git installations and standalone archive extractions:
- Checks latest releases via GitHub API.
- Caches update queries to respect rate limits.
- Updates via Git pull (with fallback reset) if .git exists.
- Updates via HTTPS tarball download with secure extraction if Git is absent.
- Cleans up all temporary extraction artifacts automatically.
- Restarts application in-place upon completion.
Complies with zero-hardcoded-paths and zero-emoji guidelines.
"""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

APP_VERSION = "0.1.10"
GITHUB_REPO = "PlasmaDrifter/AutoLaunch"
BASE_DIR = str(Path(__file__).resolve().parent)

UPDATE_CACHE: Dict[str, Any] = {
    "last_checked": 0,
    "latest_version": "",
    "release_url": "",
    "has_update": False,
    "lock": threading.Lock(),
}


def parse_version_tuple(ver_str: str) -> Tuple[int, ...]:
    """Parses a version string like 'v0.1.5' or '0.1.5' into an integer tuple (0, 1, 5)."""
    clean = re.sub(r"^[^\d]*", "", str(ver_str).strip())
    parts = []
    for part in clean.split("."):
        digits = re.match(r"^\d+", part)
        if digits:
            parts.append(int(digits.group(0)))
        else:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer_version(latest: str, current: str = APP_VERSION) -> bool:
    """Returns True if latest version is strictly higher than current."""
    try:
        return parse_version_tuple(latest) > parse_version_tuple(current)
    except Exception:
        return False


def check_github_update(force: bool = False) -> Dict[str, Any]:
    """Queries GitHub Releases API for the latest version with in-memory caching."""
    now = time.time()
    with UPDATE_CACHE["lock"]:
        if not force and (now - UPDATE_CACHE["last_checked"] < 3600) and UPDATE_CACHE["last_checked"] > 0:
            return {
                "ok": True,
                "has_update": UPDATE_CACHE["has_update"],
                "latest_version": UPDATE_CACHE["latest_version"],
                "release_url": UPDATE_CACHE["release_url"],
                "current_version": APP_VERSION,
            }

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"AutoLaunch-UpdateChecker/{APP_VERSION}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "").strip()
            html_url = data.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases"
            has_update = bool(tag and is_newer_version(tag, APP_VERSION))

            with UPDATE_CACHE["lock"]:
                UPDATE_CACHE["last_checked"] = now
                UPDATE_CACHE["latest_version"] = tag or f"v{APP_VERSION}"
                UPDATE_CACHE["release_url"] = html_url
                UPDATE_CACHE["has_update"] = has_update

            return {
                "ok": True,
                "has_update": has_update,
                "latest_version": tag or f"v{APP_VERSION}",
                "release_url": html_url,
                "current_version": APP_VERSION,
            }
    except Exception as e:
        logging.debug(f"Update check failed: {e}")
        with UPDATE_CACHE["lock"]:
            UPDATE_CACHE["last_checked"] = now - 3300  # Retry sooner on error
            return {
                "ok": False,
                "has_update": UPDATE_CACHE["has_update"],
                "latest_version": UPDATE_CACHE["latest_version"] or f"v{APP_VERSION}",
                "release_url": UPDATE_CACHE["release_url"] or f"https://github.com/{GITHUB_REPO}/releases",
                "current_version": APP_VERSION,
                "error": str(e),
            }


def apply_self_update(target_tag: str = "") -> Dict[str, Any]:
    """Applies self-update via Git pull or secure HTTPS tarball extraction."""
    is_git = os.path.isdir(os.path.join(BASE_DIR, ".git"))

    # 1. Git-based installation mode
    if is_git:
        try:
            git_check = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if git_check.returncode == 0:
                cmd = ["git", "pull", "--ff-only"]
                res = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
                if res.returncode == 0:
                    return {"mode": "git", "message": "Updated via git pull", "tag": target_tag or "latest"}

                fetch_res = subprocess.run(
                    ["git", "fetch", "--prune", "--tags", "origin"],
                    cwd=BASE_DIR,
                    capture_output=True,
                    text=True,
                )
                if fetch_res.returncode == 0:
                    branch_res = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        cwd=BASE_DIR,
                        capture_output=True,
                        text=True,
                    )
                    branch = branch_res.stdout.strip() or "master"
                    reset_res = subprocess.run(
                        ["git", "reset", "--hard", f"origin/{branch}"],
                        cwd=BASE_DIR,
                        capture_output=True,
                        text=True,
                    )
                    if reset_res.returncode == 0:
                        return {
                            "mode": "git-reset",
                            "message": f"Updated via git reset to origin/{branch}",
                            "tag": target_tag or "latest",
                        }
        except Exception as e:
            logging.debug(f"Git update failed, falling back to archive mode: {e}")

    # 2. Archive-based installation mode (No git required)
    if not target_tag:
        info = check_github_update(force=True)
        target_tag = info.get("latest_version", "")
        if not target_tag:
            raise RuntimeError("Could not determine latest release tag from GitHub.")

    clean_tag = target_tag if target_tag.startswith("v") else f"v{target_tag}"
    archive_url = f"https://github.com/{GITHUB_REPO}/archive/refs/tags/{clean_tag}.tar.gz"

    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_file = os.path.join(tmp_dir, "release.tar.gz")
        extracted_dir = os.path.join(tmp_dir, "extracted")
        os.makedirs(extracted_dir, exist_ok=True)

        req = urllib.request.Request(
            archive_url,
            headers={"User-Agent": f"AutoLaunch-SelfUpdater/{APP_VERSION}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp, open(archive_file, "wb") as f_out:
                shutil.copyfileobj(resp, f_out)
        except Exception:
            fallback_url = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/master.tar.gz"
            req_fb = urllib.request.Request(
                fallback_url,
                headers={"User-Agent": f"AutoLaunch-SelfUpdater/{APP_VERSION}"},
            )
            with urllib.request.urlopen(req_fb, timeout=30) as resp, open(archive_file, "wb") as f_out:
                shutil.copyfileobj(resp, f_out)

        with tarfile.open(archive_file, "r:gz") as tar:
            if hasattr(tarfile, "data_filter"):
                tar.extractall(path=extracted_dir, filter="data")
            else:
                for member in tar.getmembers():
                    dest_path = os.path.join(extracted_dir, member.name)
                    if os.path.commonpath([extracted_dir, os.path.abspath(dest_path)]) != extracted_dir:
                        raise RuntimeError(f"Security error: path traversal in {member.name}")
                tar.extractall(path=extracted_dir)

        subdirs = [
            os.path.join(extracted_dir, d)
            for d in os.listdir(extracted_dir)
            if os.path.isdir(os.path.join(extracted_dir, d))
        ]
        source_root = subdirs[0] if subdirs else extracted_dir

        for item in os.listdir(source_root):
            src = os.path.join(source_root, item)
            dst = os.path.join(BASE_DIR, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        return {"mode": "archive", "message": f"Updated to {target_tag} from archive", "tag": target_tag}


def restart_application() -> None:
    """Restarts the AutoLaunch application in-place with the current interpreter."""
    def _do_restart():
        time.sleep(0.5)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    t = threading.Thread(target=_do_restart, daemon=True)
    t.start()
