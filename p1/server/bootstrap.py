"""Create a disposable, user-owned Linux qualification environment.

Invoke only after server access and storage use have been agreed. The candidate
versions are source-compatible choices, not a claim of GPU validation.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv
import urllib.request
from urllib.parse import urlparse

from .support import ROOT, save_new


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory", type=Path, required=True)
    args = p.parse_args()
    if not sys.platform.startswith("linux") or sys.version_info[:2] != (3, 12):
        p.error("Use a user-owned Linux Python 3.12; do not alter system Python")
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        p.error("Never install or run this experiment as root")
    target = args.directory.resolve()
    if target.exists() or ROOT / ".runtime" not in target.parents:
        p.error("Use a new directory under this checkout's .runtime")
    target.mkdir(parents=True)
    (target / "tmp").mkdir()
    save_new(target / "runtime-registration.json", {"root": str(target), "purpose": "bounded P1 server qualification", "cleanup": "after preserving logs and lock"})
    env = os.environ.copy()
    env.update(PIP_CACHE_DIR=str(target / "cache"), TMPDIR=str(target / "tmp"), PIP_NO_COMPILE="1", PYTHONDONTWRITEBYTECODE="1")
    has_ensurepip = importlib.util.find_spec("ensurepip") is not None
    venv.EnvBuilder(with_pip=has_ensurepip).create(target / "venv")
    py = str(target / "venv/bin/python")
    if not has_ensurepip:
        # Ubuntu can provide venv without ensurepip. Bootstrap only this venv
        # from the official PyPI wheel, without apt or changing system Python.
        metadata_url = "https://pypi.org/pypi/pip/25.0.1/json"
        with urllib.request.urlopen(metadata_url, timeout=60) as response:
            metadata = json.load(response)
        wheel_info = next(item for item in metadata["urls"]
                          if item["filename"] == "pip-25.0.1-py3-none-any.whl")
        if urlparse(wheel_info["url"]).hostname != "files.pythonhosted.org":
            raise ValueError("Unexpected pip wheel host")
        with urllib.request.urlopen(wheel_info["url"], timeout=120) as response:
            wheel_bytes = response.read()
        wheel_hash = hashlib.sha256(wheel_bytes).hexdigest()
        if wheel_hash != wheel_info["digests"]["sha256"]:
            raise ValueError("PyPI pip wheel hash mismatch")
        wheel = target / "tmp" / wheel_info["filename"]
        wheel.write_bytes(wheel_bytes)
        save_new(target / "pip-bootstrap-source.json", {
            "metadata_url": metadata_url, "wheel_url": wheel_info["url"],
            "sha256": wheel_hash, "scope": "this venv only"})
        bootstrap_env = dict(env, PYTHONPATH=str(wheel))
        with (target / "pip-bootstrap.log").open("x") as log:
            subprocess.run([py, "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
                           env=bootstrap_env, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=120)
    source = target / "tmp/mdlearn-build"
    shutil.copytree(ROOT / "vendor/mdlearn-938cb80", source)
    commands = [
        [py, "-m", "pip", "install", "setuptools==75.8.2", "wheel==0.45.1"],
        [py, "-m", "pip", "install", "torch==2.7.1", "--index-url", "https://download.pytorch.org/whl/cu128"],
        [py, "-m", "pip", "install", "--only-binary=:all:", "-r", str(ROOT / "configs/p1-server-requirements.txt")],
        [py, "-m", "pip", "install", "--only-binary=:all:", "openmm[cuda12]==8.5.2"],
        [py, "-m", "pip", "install", "--no-deps", "--no-build-isolation", str(source)],
        [py, "-m", "pip", "check"],
    ]
    save_new(target / "install-commands.json", commands)
    with (target / "install.log").open("x") as log:
        for cmd in commands:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1800)
    lock = subprocess.run([py, "-m", "pip", "freeze", "--all"], capture_output=True, text=True, check=True)
    (target / "requirements.lock.txt").write_text(lock.stdout)
    print(json.dumps({"python": py, "status": "installed_not_gpu_validated", "next": "inspect, explicit GPU assignment, component CUDA validation"}))


if __name__ == "__main__":
    main()
