#!/usr/bin/env python3
"""Compare local MobileGestalt exports without printing device-specific values."""

import argparse
import json
import plistlib
from pathlib import Path


REGION = "h63QSdBCiT/z0WU6rdQv6Q"
AI = "A62OafQ85EJAiiqKn4agtg"
PROOF = "GestaltXDeviceProof"
MAX_BYTES = 16 * 1024 * 1024
KNOWN_KEYS = {REGION: "RegionCode", AI: "AppleIntelligenceCapability"}


def load_document(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Plist exceeds the supported size limit")
    data = path.read_bytes()
    if len(data) > MAX_BYTES:
        raise ValueError("Plist exceeds the supported size limit")
    document = plistlib.loads(data)
    if not isinstance(document, dict) or not isinstance(document.get("CacheExtra"), dict):
        raise ValueError("Expected a MobileGestalt document with CacheExtra")
    # This comparison does not possess the device-only HMAC key.
    proof_present = PROOF in document
    document.pop(PROOF, None)
    return document, proof_present


def same(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[key], b[key]) for key in a)
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def safe_value(value):
    if type(value) is int and -10 <= value <= 10:
        return value
    if isinstance(value, str) and value in ("CH", "ZA", "LL", "TA", "J", "B", "C"):
        return value
    return None if value is None else "redacted"


def compare_documents(before, after, before_proof=False, after_proof=False):
    old, new = before["CacheExtra"], after["CacheExtra"]
    changed = {key for key in old.keys() | new.keys()
               if (key in old) != (key in new) or not same(old.get(key), new.get(key))}
    root_changes = {key for key in before.keys() | after.keys()
                    if (key in before) != (key in after) or not same(before.get(key), after.get(key))}
    data_valid = isinstance(before.get("CacheData"), bytes) and bool(before["CacheData"])
    uuid_valid = isinstance(before.get("CacheUUID"), str) and bool(before["CacheUUID"])
    version_present = "CacheVersion" in before
    result = {
        "known_field_values": {label: {
            "before_present": key in old, "after_present": key in new,
            "before": safe_value(old.get(key)), "after": safe_value(new.get(key)),
        } for key, label in KNOWN_KEYS.items()},
        "changed_known_cache_extra_fields": [KNOWN_KEYS[key] for key in sorted(changed & KNOWN_KEYS.keys())],
        "changed_cache_extra_key_count": len(changed),
        "unexpected_cache_extra_key_count": len(changed - KNOWN_KEYS.keys()),
        "unexpected_root_key_change_count": len(root_changes - {"CacheExtra"}),
        "cache_data_unchanged": data_valid and same(before.get("CacheData"), after.get("CacheData")),
        "cache_uuid_unchanged": uuid_valid and same(before.get("CacheUUID"), after.get("CacheUUID")),
        "cache_version_unchanged": version_present and same(before.get("CacheVersion"), after.get("CacheVersion")),
        "device_proof_present": {"before": before_proof, "after": after_proof},
        "device_proof_cryptographically_verified": False,
        "files_modified": False,
    }
    result["expected_siri_changes_verified"] = (
        old.get(REGION) == "CH" and new.get(REGION) == "ZA" and AI not in old
        and type(new.get(AI)) is int and new.get(AI) == 1
        and changed == {REGION, AI} and root_changes == {"CacheExtra"}
        and result["cache_data_unchanged"] and result["cache_uuid_unchanged"]
        and result["cache_version_unchanged"]
    )
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--expected-siri", action="store_true",
                        help="Require exactly the recorded CH-to-ZA plus absent-to-1 AI override")
    args = parser.parse_args(argv)
    try:
        before, before_proof = load_document(args.before)
        after, after_proof = load_document(args.after)
        result = compare_documents(before, after, before_proof, after_proof)
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 2 if args.expected_siri and not result["expected_siri_changes_verified"] else 0
    except Exception as error:
        print(json.dumps({"status": "comparison_failed", "error_type": type(error).__name__}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
