#!/usr/bin/env python3
"""Plan or run a bounded USB session using a pinned, separately installed bridge."""

import argparse
import asyncio
import contextlib
import ctypes
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import logging
import math
import os
from pathlib import Path
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace


PACKAGE = "iap2_location_bridge_windows"
PINNED_COMMIT = "3d0af910ac6868df99978f593adb2fcbd2de8cc1"
HASHES = {
    "auth.py": "65119cf3fa9c605a80766a8a911b307b7461de649c8a350506d25705204de17a",
    "cli.py": "f673a91df7dcad147fe44b7b6f1be41321cf5affea0520964961eddb22dbe048",
    "link.py": "aef98afc77dbc6d1d0d99b395b1c24c61d8c380a45c0666e5cee7c76780ab62b",
    "profile.py": "ba0c51b1f280467a675c7ba1df83f08a71a66c9147031eed027ff3ee378de468",
    "transport.py": "6d2a411a9721080035c2ced15badfe9d0d6b505b84b3907b9277ce719c74f187",
    "wire.py": "6347139ee1103102de2ef1395cf05b4858b78a77daaa414ffc9b233330928673",
    "__init__.py": "2db7e085dff52ed97c483053741dfbd1709ab27ca6f7195b54af97fdaaf22f1f",
}
PATCHED_PROFILE = "9e89672466795781beb64fb4b8bead8551e78f48eacc8397ea48feda40ac30b3"
HELPER_HASH = "27864d741043ba4b672652226ab6fd0fa1bf440ede326645767ffc6fcaa415d2"
ALLOWED_FIELDS = {
    "event", "mode", "status", "error_type", "transport", "control_session", "identifier",
    "parameters", "sentences", "count", "attempt", "identified", "authenticated",
    "location_packets_acknowledged", "phone_location_verified", "real_location_verified",
    "manual_real_location_check_required", "reason", "duration_seconds", "hard_timeout_seconds",
    "coordinates_supplied", "identity_configured", "upstream_identity", "bridge_source_verified",
    "pinned_commit", "helper_processes_contained", "exit_code",
    "usb_device_count",
}


class UnsupportedBridgeError(ValueError):
    pass


def emit(**event):
    print(json.dumps({key: value for key, value in event.items() if key in ALLOWED_FIELDS}), flush=True)


def validate_coordinates(latitude, longitude):
    if latitude is None or longitude is None:
        raise ValueError("Explicit latitude and longitude are required for send mode")
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be finite and between -90 and 90")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be finite and between -180 and 180")


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("The pinned bridge must contain regular source files")
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def validate_bridge(root):
    root = root.resolve()
    source = root / "src" / PACKAGE
    for name, expected in HASHES.items():
        actual = digest(source / name)
        if actual != expected and not (name == "profile.py" and actual == PATCHED_PROFILE):
            raise UnsupportedBridgeError("Unsupported bridge source; use the pinned upstream commit")
    if digest(root / "tools/local_mfi_v3_helper.py") != HELPER_HASH:
        raise UnsupportedBridgeError("Authentication helper differs from the pinned source")
    return root


class SourceOnlyLoader(importlib.machinery.SourceFileLoader):
    def get_code(self, fullname):
        return self.source_to_code(self.get_data(self.path), self.path)


class PinnedFinder(importlib.abc.MetaPathFinder):
    def __init__(self, root):
        self.directory = root / "src" / PACKAGE

    def find_spec(self, fullname, path=None, target=None):
        if fullname != PACKAGE and not fullname.startswith(PACKAGE + "."):
            return None
        name = "__init__.py" if fullname == PACKAGE else fullname[len(PACKAGE) + 1:] + ".py"
        if name not in HASHES:
            raise ImportError("Unrecognized bridge module")
        filename = self.directory / name
        loader = SourceOnlyLoader(fullname, str(filename))
        return importlib.util.spec_from_file_location(
            fullname, filename, loader=loader,
            submodule_search_locations=[str(self.directory)] if fullname == PACKAGE else None,
        )


def use_upstream_identity(bridge):
    wire = importlib.import_module(PACKAGE + ".wire")
    original = bridge.identity
    names = ("Accessory Location Lab", "AL-1", "Local Research", "AL-LOCAL-001", "0.1", "1")

    def identity(transport="usb", bluetooth_address=None):
        message = original(transport, bluetooth_address)
        body = b"".join(wire.text_parameter(key, names[key]) if key < len(names)
                        else wire.parameter(key, value)
                        for key, value in wire.parameters(message.body))
        return wire.Message(message.identifier, body)

    bridge.identity = identity


async def bounded_operation(operation, control_file, timeout):
    task = asyncio.create_task(operation)
    reason = "completed"
    async def stopped():
        while not control_file.exists():
            await asyncio.sleep(0.1)
    stop = asyncio.create_task(stopped())
    try:
        done, _ = await asyncio.wait({task, stop}, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
        if task in done:
            await task
        elif stop in done:
            reason = "stop_requested"
            emit(event="stop_requested")
        else:
            reason = "session_timeout"
            emit(event="session_timeout")
    finally:
        stop.cancel()
        if not task.done():
            task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        with contextlib.suppress(asyncio.CancelledError):
            await stop
    return reason


async def service_probe(create_phone):
    phone = await create_phone(connection_type="USB", autopair=False)
    try:
        emit(event="device_connected", transport="usb")
        stream = await phone.start_lockdown_service("com.apple.carkit.service")
        try:
            emit(event="carkit_service_opened")
        finally:
            await stream.close()
    finally:
        await phone.close()


async def connect_one_usb(list_devices, create_phone):
    devices = [device for device in await list_devices() if device.connection_type == "USB"]
    emit(event="usb_device_count", usb_device_count=len(devices))
    if len(devices) != 1:
        raise RuntimeError("Connect exactly one already trusted USB device")
    return await create_phone(serial=devices[0].serial, connection_type="USB", autopair=False)


async def worker(args):
    # The parent assigns process containment before releasing this gate.
    if os.environ.get("APPLE_FEATURE_LAB_WORKER") != "1" or sys.stdin.readline().strip() != "start":
        raise RuntimeError("Worker must be started by its supervisor")
    logging.disable(logging.CRITICAL)
    root = validate_bridge(args.bridge_root)
    sys.meta_path.insert(0, PinnedFinder(root))
    bridge = importlib.import_module(PACKAGE + ".cli")
    usbmux = importlib.import_module("pymobiledevice3.usbmux")
    original_create = bridge.create_using_usbmux
    async def create_checked_phone(**options):
        return await connect_one_usb(usbmux.list_devices, original_create)
    bridge.create_using_usbmux = create_checked_phone
    final_state = {}
    def bridge_event(**event):
        if event.get("event") == "finished":
            final_state.update(event)
        emit(**event)
    bridge.emit = bridge_event
    if args.upstream_identity:
        use_upstream_identity(bridge)
    credentials = {
        "IAP2_LOCATION_BRIDGE_WINDOWS_CERT_FILE": str(args.cert_file.resolve()) if args.cert_file else None,
        "IAP2_LOCATION_BRIDGE_WINDOWS_KEY_FILE": str(args.key_file.resolve()) if args.key_file else None,
    }
    previous = {key: os.environ.get(key) for key in credentials}
    try:
        for key, value in credentials.items():
            if value is not None:
                os.environ[key] = value
        if args.mode == "service-probe":
            operation = service_probe(bridge.create_using_usbmux)
        else:
            options = SimpleNamespace(
                command="send" if args.mode == "send" else "probe", transport="usb",
                auth_helper=str(root / "tools/local_mfi_v3_helper.py"),
                duration=args.duration, latitude=args.latitude, longitude=args.longitude, interval=1,
            )
            operation = bridge.run(options)
        reason = await bounded_operation(operation, args.control_file, max(0.1, args.timeout - 5))
        if reason == "session_timeout":
            raise TimeoutError("Operation exceeded its bounded session time")
        if reason == "completed" and args.mode in ("auth-probe", "send"):
            if not final_state.get("identified") or not final_state.get("authenticated"):
                emit(event="authentication_not_completed")
                raise RuntimeError("Authentication did not complete")
            if args.mode == "send" and not final_state.get("location_packets_acknowledged"):
                emit(event="no_location_packets_acknowledged")
                raise RuntimeError("No location packets were acknowledged")
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        emit(event="session_closed", phone_location_verified=False, real_location_verified=False,
             manual_real_location_check_required=args.mode == "send")


class WindowsJob:
    def __init__(self, process):
        from ctypes import wintypes
        size = ctypes.c_size_t
        class Basic(ctypes.Structure):
            _fields_ = [("ProcessTime", ctypes.c_int64), ("JobTime", ctypes.c_int64),
                        ("Flags", wintypes.DWORD), ("MinSet", size), ("MaxSet", size),
                        ("Active", wintypes.DWORD), ("Affinity", size),
                        ("Priority", wintypes.DWORD), ("Scheduling", wintypes.DWORD)]
        class Counters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]
        class Extended(ctypes.Structure):
            _fields_ = [("Basic", Basic), ("IO", Counters), ("ProcessMemory", size),
                        ("JobMemory", size), ("PeakProcessMemory", size), ("PeakJobMemory", size)]
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        self.api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            limits = Extended()
            limits.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                raise ctypes.WinError(ctypes.get_last_error())
            if not self.api.AssignProcessToJobObject(self.handle, wintypes.HANDLE(process._handle)):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def supervise(command, timeout, control_file, stop_file=None):
    started = time.monotonic()
    environment = dict(os.environ, APPLE_FEATURE_LAB_WORKER="1")
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                               env=environment, start_new_session=os.name != "nt",
                               creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
                               if os.name == "nt" else 0)
    job = None
    events = queue.Queue(maxsize=256)
    reason = None
    grace_deadline = None

    def read_output():
        for line in process.stdout:
            with contextlib.suppress(queue.Full):
                events.put_nowait(line)

    def drain():
        while True:
            try:
                line = events.get_nowait()
            except queue.Empty:
                break
            try:
                event = json.loads(line)
                if isinstance(event, dict):
                    emit(**event)
            except (ValueError, TypeError):
                pass

    try:
        if os.name == "nt":
            job = WindowsJob(process)
        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        process.stdin.write("start\n")
        process.stdin.flush()
        process.stdin.close()
        while process.poll() is None:
            drain()
            now = time.monotonic()
            if now - started >= timeout:
                reason = "hard_timeout"
                break
            if stop_file is not None and stop_file.exists() and reason is None:
                reason = "stop_file"
                control_file.touch()
                grace_deadline = min(started + timeout, now + 5)
            if grace_deadline is not None and now >= grace_deadline:
                break
            time.sleep(0.05)
    except KeyboardInterrupt:
        reason = "interrupted"
        control_file.touch()
        with contextlib.suppress(subprocess.TimeoutExpired, KeyboardInterrupt):
            process.wait(timeout=max(0.01, min(5, started + timeout - time.monotonic())))
    finally:
        if job is not None:
            job.close()
        elif os.name != "nt":
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        elif process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        if process.stdout:
            # Kill containment also closes inherited pipes held by helpers.
            reader.join(timeout=1) if "reader" in locals() else None
        drain()
        if process.stdout:
            process.stdout.close()
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
    if reason:
        emit(event="supervisor_stopped", reason=reason, helper_processes_contained=True,
             real_location_verified=False, manual_real_location_check_required=True)
        return 124 if reason == "hard_timeout" else 130 if reason == "interrupted" else 0
    return process.returncode


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["plan", "service-probe", "auth-probe", "send"], default="plan")
    parser.add_argument("--bridge-root", type=Path)
    parser.add_argument("--cert-file", type=Path)
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--duration", type=int)
    parser.add_argument("--timeout", type=float)
    parser.add_argument("--stop-file", type=Path)
    parser.add_argument("--upstream-identity", action="store_true")
    parser.add_argument("--internal-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--control-file", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    args.duration = args.duration if args.duration is not None else 20 if args.mode == "auth-probe" else 180
    args.timeout = args.timeout if args.timeout is not None else 30 if args.mode == "service-probe" else args.duration + 45
    if not 1 <= args.duration <= 600 or not math.isfinite(args.timeout) or not 1 <= args.timeout <= 660:
        parser.error("duration must be 1..600 seconds and timeout 1..660 seconds")
    if args.mode == "send":
        try:
            validate_coordinates(args.latitude, args.longitude)
        except ValueError as error:
            parser.error(str(error))
    if args.mode != "plan":
        if args.bridge_root is None:
            parser.error("--bridge-root is required for execution")
        if args.mode in ("auth-probe", "send") and not (args.cert_file and args.key_file):
            parser.error("auth-probe/send require explicit --cert-file and --key-file")
        for path in (args.cert_file, args.key_file):
            if path is not None and (path.is_symlink() or not path.is_file()):
                parser.error("Identity paths must be regular local files")
    if args.stop_file is not None and args.stop_file.exists():
        parser.error("Stop file already exists; inspect the previous session before choosing a new path")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.bridge_root is not None:
            args.bridge_root = validate_bridge(args.bridge_root)
        if args.mode == "plan":
            emit(event="plan", mode=args.mode, duration_seconds=args.duration,
                 hard_timeout_seconds=args.timeout, coordinates_supplied=args.latitude is not None and args.longitude is not None,
                 identity_configured=bool(args.cert_file and args.key_file),
                 upstream_identity=args.upstream_identity, bridge_source_verified=args.bridge_root is not None,
                 pinned_commit=PINNED_COMMIT, phone_location_verified=False,
                 manual_real_location_check_required=True)
            return 0
        if args.internal_worker:
            if args.control_file is None:
                raise ValueError("Missing supervisor control path")
            asyncio.run(worker(args))
            return 0
        with tempfile.TemporaryDirectory(prefix="apple-feature-lab-") as directory:
            control = Path(directory) / "stop"
            original = list(sys.argv[1:] if argv is None else argv)
            command = [sys.executable, "-u", str(Path(__file__).resolve()), *original,
                       "--internal-worker", "--control-file", str(control)]
            return supervise(command, args.timeout, control, args.stop_file)
    except ImportError:
        emit(event="missing_dependency", status="install_pinned_bridge_dependencies_in_the_current_python_environment")
        return 2
    except TimeoutError:
        emit(event="operation_timeout", real_location_verified=False)
        return 124
    except UnsupportedBridgeError:
        emit(event="execution_failed", error_type="UnsupportedBridgeError", reason="unsupported_bridge_source")
        return 2
    except Exception as error:
        emit(event="execution_failed", error_type=type(error).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
