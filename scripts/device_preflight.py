#!/usr/bin/env python3
"""Read a small, identifier-free summary from one already trusted USB device."""

import asyncio
import json
import logging


def emit(**data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


async def inspect_device(list_devices, create_phone):
    devices = await list_devices()
    usb = [device for device in devices if device.connection_type == "USB"]
    result = {"usb_device_count": len(usb), "device_settings_changed": False}
    if len(usb) != 1:
        result["status"] = "connect_exactly_one_trusted_usb_device"
        return result, 2
    phone = await create_phone(connection_type="USB", autopair=False)
    try:
        result["device"] = {}
        for key in ("ProductType", "ProductVersion", "BuildVersion"):
            result["device"][key] = await phone.get_value(key=key)
        for name, domain, key in (
            ("developer_mode_enabled", "com.apple.security.mac.amfi", "DeveloperModeStatus"),
            ("backup_encryption_enabled", "com.apple.mobile.backup", "WillEncrypt"),
        ):
            try:
                value = await phone.get_value(domain=domain, key=key)
                result[name] = bool(value) if value is not None else None
            except Exception as error:
                result[name] = None
                result[name + "_read_error"] = type(error).__name__
        result["status"] = "read_complete"
        return result, 0
    finally:
        await asyncio.wait_for(phone.close(), timeout=5)


def main():
    logging.disable(logging.CRITICAL)
    try:
        from pymobiledevice3.lockdown import create_using_usbmux
        from pymobiledevice3.usbmux import list_devices
    except ImportError:
        emit(status="missing_dependency", install="python -m pip install 'pymobiledevice3>=9.40,<10'")
        return 2
    try:
        report, code = asyncio.run(asyncio.wait_for(
            inspect_device(list_devices, create_using_usbmux), timeout=30))
        emit(**report)
        return code
    except KeyboardInterrupt:
        emit(status="interrupted")
        return 130
    except Exception as error:
        emit(status="read_failed", error_type=type(error).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
