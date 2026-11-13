"""Lightweight iOS location spoofer built on pymobiledevice3 (USB).

Picks the right backend for the connected device:
  * iOS < 17  -> `developer simulate-location` (one-shot; stays until cleared)
  * iOS >= 17 -> `developer dvt simulate-location` (holds a session open;
                 the spoofed location lasts only while this script runs)
"""

import argparse
import asyncio
import subprocess
import sys
import time

PMD3 = [sys.executable, "-m", "pymobiledevice3"]

# Windows consoles default to cp1252, which can't print the status emoji.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def run_pmd3(*args: str, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run([*PMD3, *args], capture_output=capture, text=True)


def get_ios_major() -> int:
    from pymobiledevice3.lockdown import create_using_usbmux

    async def _version() -> str:
        lockdown = await create_using_usbmux()
        return lockdown.product_version

    try:
        version = asyncio.run(_version())
    except Exception as exc:  # noqa: BLE001 - surface any connection failure
        print(f"❌ Could not connect to an iPhone over USB: {exc}")
        print("Check the cable, unlock the phone, tap 'Trust This Computer'.")
        print("On Windows, the Apple Devices app (or iTunes) must be installed for usbmuxd.")
        sys.exit(1)
    print(f"📱 Connected device runs iOS {version}")
    return int(version.split(".")[0])


def mount_ddi() -> None:
    print("Mounting Developer Disk Image (no-op if already mounted)...")
    result = run_pmd3("mounter", "auto-mount")
    out = (result.stdout + result.stderr).strip()
    if result.returncode != 0 and "already mounted" not in out.lower():
        print(f"⚠️  auto-mount reported a problem:\n{out}")
        print("Is Developer Mode enabled? (Settings > Privacy & Security > Developer Mode)")


# ---------- iOS < 17 ----------

def legacy_set(lat: float, lon: float) -> bool:
    # `--` stops negative numbers (e.g. -122.4) being parsed as options.
    result = run_pmd3("developer", "simulate-location", "set", "--", str(lat), str(lon))
    if result.returncode == 0:
        print(f"✅ Location set to {lat}, {lon}")
        return True
    print(f"❌ Failed to set location:\n{result.stderr.strip()}")
    return False


def legacy_clear() -> None:
    run_pmd3("developer", "simulate-location", "clear")
    print("✅ Real location restored.")


def run_legacy(lat: float, lon: float, auto: bool) -> None:
    if not auto:
        legacy_set(lat, lon)
        print("Restore later with: uv run python location_spoofer.py --clear")
        return
    print("🚀 Auto-refresh every 60s. Press Ctrl+C to stop and restore real location.")
    try:
        while True:
            legacy_set(lat, lon)
            time.sleep(60)
    except KeyboardInterrupt:
        print()
        legacy_clear()


# ---------- iOS >= 17 ----------

def modern_clear() -> None:
    run_pmd3("developer", "dvt", "simulate-location", "clear")
    print("✅ Real location restored.")


def run_modern(lat: float, lon: float, auto: bool) -> None:
    cmd = [*PMD3, "developer", "dvt", "simulate-location", "set", "--", str(lat), str(lon)]
    print(f"Setting location to {lat}, {lon} (iOS 17+ session).")
    print("Keep this window open; press Ctrl+C to stop and restore real location.")
    try:
        while True:
            # pymobiledevice3 waits on "Press ENTER to exit"; give it a stdin
            # that never closes so the session lasts until Ctrl+C.
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            code = proc.wait()
            if not auto:
                print(f"Session ended (exit code {code}).")
                break
            print(f"⚠️  Session dropped (exit code {code}); reconnecting in 5s...")
            time.sleep(5)
    except KeyboardInterrupt:
        print()
        try:
            proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, NameError):
            pass
    modern_clear()


def main() -> None:
    parser = argparse.ArgumentParser(description="Lightweight iOS Location Spoofer")
    parser.add_argument("--lat", type=float, help="Target latitude")
    parser.add_argument("--lon", type=float, help="Target longitude")
    parser.add_argument("--auto", action="store_true",
                        help="Keep the spoof alive: refresh every 60s (iOS<17) "
                             "or reconnect if the session drops (iOS 17+)")
    parser.add_argument("--clear", action="store_true", help="Restore the real location and exit")
    parser.add_argument("--no-mount", action="store_true", help="Skip the automatic DDI mount")
    args = parser.parse_args()

    if not args.clear and (args.lat is None or args.lon is None):
        parser.error("--lat and --lon are required (or use --clear)")

    major = get_ios_major()

    if args.clear:
        modern_clear() if major >= 17 else legacy_clear()
        return

    if not args.no_mount:
        mount_ddi()

    if major >= 17:
        run_modern(args.lat, args.lon, args.auto)
    else:
        run_legacy(args.lat, args.lon, args.auto)


if __name__ == "__main__":
    main()
