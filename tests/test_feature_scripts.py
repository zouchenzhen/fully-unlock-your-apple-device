"""Offline checks: no USB access, account login, or location transmission."""

import asyncio
import contextlib
import ctypes
import importlib.util
import io
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preflight = load("device_preflight")
verify = load("verify_mobilegestalt")
location = load("run_iap2_location")


class PreflightTests(unittest.IsolatedAsyncioTestCase):
    async def test_queries_only_allowlisted_fields_and_closes(self):
        calls = []
        class Phone:
            closed = False
            async def get_value(self, domain=None, key=None):
                calls.append((domain, key))
                return {"ProductType": "iPhone18,1", "ProductVersion": "27.3", "BuildVersion": "24C5037i",
                        "DeveloperModeStatus": True, "WillEncrypt": True}[key]
            async def close(self):
                self.closed = True
        phone = Phone()
        async def devices():
            return [SimpleNamespace(connection_type="USB", serial="SECRET_UDID")]
        async def create(**options):
            self.assertEqual(options, {"connection_type": "USB", "autopair": False})
            return phone
        result, code = await preflight.inspect_device(devices, create)
        self.assertEqual(code, 0)
        self.assertTrue(phone.closed)
        self.assertNotIn("SECRET_UDID", json.dumps(result))
        self.assertEqual({key for _, key in calls}, {
            "ProductType", "ProductVersion", "BuildVersion", "DeveloperModeStatus", "WillEncrypt"})

    async def test_multiple_usb_devices_does_not_connect(self):
        async def devices():
            return [SimpleNamespace(connection_type="USB"), SimpleNamespace(connection_type="USB")]
        async def forbidden(**options):
            self.fail("must not select a device implicitly")
        result, code = await preflight.inspect_device(devices, forbidden)
        self.assertEqual((result["usb_device_count"], code), (2, 2))

    async def test_read_failure_still_closes(self):
        class Phone:
            closed = False
            async def get_value(self, **options):
                raise RuntimeError("SECRET_UDID")
            async def close(self):
                self.closed = True
        phone = Phone()
        async def devices():
            return [SimpleNamespace(connection_type="USB")]
        async def create(**options):
            return phone
        with self.assertRaises(RuntimeError):
            await preflight.inspect_device(devices, create)
        self.assertTrue(phone.closed)


class PlistTests(unittest.TestCase):
    def baseline(self):
        return {"CacheUUID": "DEVICE-SECRET-UUID", "CacheVersion": 7, "CacheData": b"\x00\x01\x02",
                "CacheExtra": {verify.REGION: "CH", "SerialNumber": "SECRET-SERIAL", "Private": "owner@example.invalid"}}

    def changed(self):
        result = self.baseline()
        result["CacheExtra"][verify.REGION] = "ZA"
        result["CacheExtra"][verify.AI] = 1
        return result

    def test_expected_change_and_proof_comparison_leave_files_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            before, after = Path(directory) / "before.plist", Path(directory) / "after.plist"
            changed = self.changed()
            changed[verify.PROOF] = {"tag": b"SECRET-TAG"}
            before.write_bytes(plistlib.dumps(self.baseline()))
            after.write_bytes(plistlib.dumps(changed))
            original_bytes = (before.read_bytes(), after.read_bytes())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = verify.main([str(before), str(after), "--expected-siri"])
            result = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertTrue(result["expected_siri_changes_verified"])
            self.assertFalse(result["device_proof_cryptographically_verified"])
            self.assertEqual((before.read_bytes(), after.read_bytes()), original_bytes)
            for secret in ("SECRET", "owner@example.invalid", str(before), str(after)):
                self.assertNotIn(secret, output.getvalue())

    def test_unknown_field_and_root_changes_fail_strict_check(self):
        changed = self.changed()
        changed["CacheExtra"]["Private"] = "NEW-SECRET"
        changed["NewRoot"] = "PRIVATE"
        report = verify.compare_documents(self.baseline(), changed)
        self.assertFalse(report["expected_siri_changes_verified"])
        self.assertEqual(report["unexpected_cache_extra_key_count"], 1)
        self.assertEqual(report["unexpected_root_key_change_count"], 1)
        self.assertNotIn("NEW-SECRET", json.dumps(report))

    def test_boolean_does_not_pass_as_expected_integer(self):
        changed = self.changed()
        changed["CacheExtra"][verify.AI] = True
        self.assertFalse(verify.compare_documents(self.baseline(), changed)["expected_siri_changes_verified"])

    def test_missing_cache_identity_cannot_pass(self):
        before, after = self.baseline(), self.changed()
        for item in (before, after):
            item.pop("CacheData")
            item.pop("CacheUUID")
        self.assertFalse(verify.compare_documents(before, after)["expected_siri_changes_verified"])

    def test_different_region_is_reported_without_calling_it_siri_success(self):
        changed = self.changed()
        changed["CacheExtra"][verify.REGION] = "LL"
        report = verify.compare_documents(self.baseline(), changed)
        self.assertEqual(report["known_field_values"]["RegionCode"]["after"], "LL")
        self.assertFalse(report["expected_siri_changes_verified"])

    def test_corrupt_input_returns_nonzero_without_echoing_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "SECRET-PATH.plist"
            path.write_bytes(b"not a plist")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(verify.main([str(path), str(path)]), 1)
            self.assertNotIn("SECRET-PATH", output.getvalue())


class LocationTests(unittest.TestCase):
    def test_coordinate_boundaries_and_invalid_values(self):
        for latitude, longitude in ((90, 180), (-90, -180), (0, 0), (52.52, 13.405)):
            location.validate_coordinates(latitude, longitude)
        for latitude, longitude in ((None, 1), (91, 0), (0, -181), (float("nan"), 0), (0, float("inf"))):
            with self.assertRaises(ValueError):
                location.validate_coordinates(latitude, longitude)

    def test_plan_does_not_import_usb_library(self):
        code = """import sys, runpy, importlib.abc
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('pymobiledevice3'):
            raise RuntimeError('USB IMPORT FORBIDDEN')
sys.meta_path.insert(0, Deny())
path = sys.argv[1]
sys.argv = [path]
runpy.run_path(path, run_name='__main__')
"""
        completed = subprocess.run([sys.executable, "-c", code, str(ROOT / "scripts/run_iap2_location.py")],
                                   capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["event"], "plan")

    def test_unknown_bridge_fails_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                location.validate_bridge(Path(directory))

    def test_changed_bridge_reports_fixed_reason_without_path(self):
        with tempfile.TemporaryDirectory(prefix="private-bridge-") as directory:
            source = Path(directory) / "src" / location.PACKAGE
            source.mkdir(parents=True)
            (source / "auth.py").write_text("unrecognized code", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = location.main(["--bridge-root", directory])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(output.getvalue())["reason"], "unsupported_bridge_source")
            self.assertNotIn(directory, output.getvalue())

    def test_send_rejects_missing_identity_and_coordinates(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                location.parse_args(["--mode", "send", "--bridge-root", "."])

    def test_supervisor_timeout_kills_worker_and_its_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            marker, control = directory / "helper.pid", directory / "stop"
            worker = directory / "mock_worker.py"
            worker.write_text(
                "import sys,subprocess,time,pathlib\n"
                "sys.stdin.readline()\n"
                "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
                "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
                "time.sleep(60)\n", encoding="utf-8")
            started = time.monotonic()
            with contextlib.redirect_stdout(io.StringIO()):
                code = location.supervise([sys.executable, str(worker), str(marker)], 1.2, control)
            self.assertEqual(code, 124)
            self.assertLess(time.monotonic() - started, 5)
            self.assertTrue(marker.exists())
            helper = int(marker.read_text())
            if os.name == "nt":
                api = ctypes.WinDLL("kernel32", use_last_error=True)
                api.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
                api.OpenProcess.restype = ctypes.c_void_p
                handle = api.OpenProcess(0x1000, False, helper)
                if handle:
                    status = ctypes.c_uint32()
                    api.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
                    api.CloseHandle.argtypes = [ctypes.c_void_p]
                    api.GetExitCodeProcess(handle, ctypes.byref(status))
                    api.CloseHandle(handle)
                    self.assertNotEqual(status.value, 259)
            else:
                status = Path(f"/proc/{helper}/stat")
                if status.exists():
                    self.assertEqual(status.read_text().split()[2], "Z")


class CancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_zero_or_multiple_usb_devices_never_connect(self):
        calls = []
        async def forbidden(**options):
            calls.append(options)
            self.fail("must not connect to an ambiguous USB device")
        for count in (0, 2):
            async def devices():
                return [SimpleNamespace(connection_type="USB", serial="PRIVATE") for _ in range(count)]
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                await location.connect_one_usb(devices, forbidden)
        self.assertEqual(calls, [])

    async def test_single_usb_device_is_pinned_by_serial_without_printing_it(self):
        async def devices():
            return [SimpleNamespace(connection_type="Network", serial="OTHER"),
                    SimpleNamespace(connection_type="USB", serial="PRIVATE-SERIAL")]
        async def create(**options):
            self.assertEqual(options, {"serial": "PRIVATE-SERIAL", "connection_type": "USB", "autopair": False})
            return "phone"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(await location.connect_one_usb(devices, create), "phone")
        self.assertNotIn("PRIVATE-SERIAL", output.getvalue())

    async def test_session_timeout_runs_coroutine_cleanup(self):
        flags = []
        async def operation():
            try:
                await asyncio.sleep(60)
            finally:
                flags.append("closed")
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stdout(io.StringIO()):
                reason = await location.bounded_operation(operation(), Path(directory) / "stop", 0.02)
        self.assertEqual(reason, "session_timeout")
        self.assertEqual(flags, ["closed"])

    async def test_stop_file_runs_coroutine_cleanup(self):
        flags = []
        async def operation():
            try:
                await asyncio.sleep(60)
            finally:
                flags.append("closed")
        with tempfile.TemporaryDirectory() as directory:
            control = Path(directory) / "stop"
            async def stop():
                await asyncio.sleep(0.01)
                control.touch()
            trigger = asyncio.create_task(stop())
            with contextlib.redirect_stdout(io.StringIO()):
                reason = await location.bounded_operation(operation(), control, 1)
            await trigger
        self.assertEqual(reason, "stop_requested")
        self.assertEqual(flags, ["closed"])

    async def test_service_probe_closes_stream_and_phone(self):
        flags = []
        class Stream:
            async def close(self):
                flags.append("stream")
        class Phone:
            async def start_lockdown_service(self, name):
                self.name = name
                return Stream()
            async def close(self):
                flags.append("phone")
        async def create(**options):
            self.assertFalse(options["autopair"])
            return Phone()
        with contextlib.redirect_stdout(io.StringIO()):
            await location.service_probe(create)
        self.assertEqual(flags, ["stream", "phone"])

    async def test_worker_restores_credential_environment_on_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = SimpleNamespace(bridge_root=root, cert_file=root / "cert", key_file=root / "key",
                                   upstream_identity=False, mode="auth-probe", duration=1,
                                   latitude=None, longitude=None, control_file=root / "stop", timeout=6)
            async def fail(options):
                self.assertEqual(os.environ["IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE"], str((root / "key").resolve()))
                raise RuntimeError("private-path-secret")
            async def create(**options):
                self.fail("this error test must not connect")
            async def devices():
                return []
            bridge = SimpleNamespace(run=fail, create_using_usbmux=create)
            def imported(name):
                return bridge if name == location.PACKAGE + ".cli" else SimpleNamespace(list_devices=devices)
            previous_path = list(sys.meta_path)
            try:
                with patch.dict(os.environ, {"APPLE_FEATURE_LAB_WORKER": "1",
                                             "IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE": "original-secret"}), \
                     patch.object(sys, "stdin", io.StringIO("start\n")), \
                     patch.object(location, "validate_bridge", return_value=root), \
                     patch.object(location.importlib, "import_module", side_effect=imported), \
                     contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        await location.worker(args)
                    self.assertEqual(os.environ["IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE"], "original-secret")
            finally:
                sys.meta_path[:] = previous_path


if __name__ == "__main__":
    unittest.main()
