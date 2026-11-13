# iOS Location Spoofer

Sets a simulated GPS location on an iPhone over USB with [pymobiledevice3](https://github.com/doronz88/pymobiledevice3).

## Prerequisites
- [uv](https://docs.astral.sh/uv/)
- iPhone: **Settings > Privacy & Security > Developer Mode** turned on
- Windows: the **Apple Devices** app (or iTunes) installed, which provides the usbmuxd driver
- Phone connected by USB, unlocked, and "Trust This Computer" accepted

**Install Apple Devices from the [Microsoft Store](https://apps.microsoft.com/detail/9np83lwlpz9k?). Either search "Apple Devices" in the Store, or run this in a terminal:**

```sh
winget install 9NP83LWLPZ9K --source msstore
```

## Usage
```sh
uv sync
uv run python location_spoofer.py --lat 37.7749 --lon -122.4194          # set the location
uv run python location_spoofer.py --lat 37.7749 --lon -122.4194 --auto   # keep it alive
uv run python location_spoofer.py --clear                                # restore the real location
```
The script detects the iOS version and mounts the Developer Disk Image automatically (`--no-mount` skips this).

| iOS | Behaviour |
|-----|-----------|
| < 17 | One-shot `set` that stays until cleared. `--auto` re-applies it every 60s. |
| 17+ | Holds a DVT session open. **The spoof lasts only while the script runs.** Ctrl+C restores the real location. `--auto` reconnects if the session drops. |

## Troubleshooting
- `Failed to connect to usbmuxd socket`: install or open the Apple Devices app or iTunes, then reconnect the phone.
- DDI mount fails: confirm Developer Mode is on and the phone has been rebooted after enabling it.
- Run any pymobiledevice3 command directly, e.g. `uv run pymobiledevice3 usbmux list`.
