#!/usr/bin/env python3
"""Restore upstream identity strings in the pinned Windows bridge profile."""

import argparse
import hashlib
from pathlib import Path


EXPECTED_SHA256 = "ba0c51b1f280467a675c7ba1df83f08a71a66c9147031eed027ff3ee378de468"
PATCHED_SHA256 = "9e89672466795781beb64fb4b8bead8551e78f48eacc8397ea48feda40ac30b3"
OLD = (
    '"iAP2 Location Bridge for Windows", "ILBW-1", "iAP2 Location Bridge",\n'
    '                "ILBW-LOCAL-001", "0.1.0", "1",'
)
NEW = (
    '"Accessory Location Lab", "AL-1", "Local Research",\n'
    '                "AL-LOCAL-001", "0.1", "1",'
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help="Path to the pinned bridge's profile.py")
    args = parser.parse_args()
    path = args.profile
    if path.is_symlink() or not path.is_file() or path.name != "profile.py":
        parser.error("Supply a regular, non-symlink profile.py file")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError:
        parser.error("Expected the pinned UTF-8 source file")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if digest == PATCHED_SHA256:
        print("Upstream identity is already applied; no file changed.")
        return
    if digest != EXPECTED_SHA256 or text.count(OLD) != 1:
        parser.error("Source differs from the pinned version; no file changed")
    patched = text.replace(OLD, NEW, 1)
    if hashlib.sha256(patched.encode("utf-8")).hexdigest() != PATCHED_SHA256:
        parser.error("Patch verification failed; no file changed")
    newline = "\r\n" if b"\r\n" in raw else "\n"
    path.write_bytes(patched.replace("\n", newline).encode("utf-8"))
    print("Restored the six upstream identity strings.")


if __name__ == "__main__":
    main()
