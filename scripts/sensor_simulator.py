#!/usr/bin/env python3
"""Simulate real-time sensor data from MPU-6050, HW-485, and HW-509 and POST to the engine.

Hotkeys (toggle anomaly mode per sensor):
  G  →  gyro    (MPU-6050)
  S  →  sound   (HW-485)
  M  →  magnetic (HW-509)

Press a key once to lock that sensor into anomaly mode; press again to return to normal.
"""

import argparse
import random
import sys
import termios
import threading
import tty
import time
import uuid
from datetime import datetime, timezone

import requests

# ── Hotkey state ─────────────────────────────────────────
_force_anomaly: dict[str, bool] = {"gyro": False, "sound": False, "magnetic": False}
_HOTKEYS = {"g": "gyro", "s": "sound", "m": "magnetic"}

# Terminal settings — saved once so we can restore on exit
_orig_term = None


def _key_listener() -> None:
    """Background thread: reads single chars from stdin in cbreak mode."""
    global _orig_term
    fd = sys.stdin.fileno()
    _orig_term = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)          # char-by-char, no echo; Ctrl+C still raises SIGINT
        while True:
            ch = sys.stdin.read(1).lower()
            if ch in _HOTKEYS:
                sensor = _HOTKEYS[ch]
                _force_anomaly[sensor] = not _force_anomaly[sensor]
                state = "\033[31mANOMALY LOCKED\033[0m" if _force_anomaly[sensor] else "\033[32mnormal\033[0m"
                print(f"\n  [hotkey] {sensor.upper():8s} → {state}")
    except Exception:
        pass


def _restore_term() -> None:
    if _orig_term is not None:
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _orig_term)
        except Exception:
            pass


_listener_thread = threading.Thread(target=_key_listener, daemon=True)
_listener_thread.start()

API_URL = "http://localhost:8000/api/v1/events"
USER = "system"

machine_id = str(uuid.uuid4())

# ── Anomaly scenarios ────────────────────────────────────

GYRO_ANOMALIES = [
    {
        "name": "impact_detected",
        "reason": "Sudden high-g impact detected — possible physical tampering or collision",
        "ax": (4, 12), "ay": (-10, -3), "az": (2, 6),
        "gx": (200, 800), "gy": (-600, -200), "gz": (100, 400),
    },
    {
        "name": "freefall",
        "reason": "Near-zero gravity on all axes — device may be in freefall or detached",
        "ax": (-0.1, 0.1), "ay": (-0.1, 0.1), "az": (-0.3, 0.3),
        "gx": (-5, 5), "gy": (-5, 5), "gz": (-5, 5),
    },
    {
        "name": "sustained_vibration",
        "reason": "Persistent high-frequency vibration — possible motor fault or structural resonance",
        "ax": (-3, 3), "ay": (-3, 3), "az": (7, 12),
        "gx": (50, 300), "gy": (50, 300), "gz": (50, 300),
    },
    {
        "name": "tilt_anomaly",
        "reason": "Device tilted beyond safe operating angle — mounting may have shifted",
        "ax": (3, 7), "ay": (3, 7), "az": (2, 5),
        "gx": (-10, 10), "gy": (-10, 10), "gz": (-10, 10),
    },
]

SOUND_ANOMALIES = [
    "Loud sound burst detected — possible glass break or explosion",
    "Sustained loud noise — possible alarm or machinery malfunction",
    "Repeated sound triggers in short interval — possible intrusion attempt",
]

MAGNETIC_ANOMALIES = [
    "Magnetic field change detected — door/enclosure may have been opened",
    "Strong magnetic interference — possible magnet-based tampering attempt",
    "Magnetic sensor triggered in restricted hours — unauthorized physical access",
]


# ── Event generators ─────────────────────────────────────

def gyro_event() -> dict:
    """MPU-6050: 3-axis accel (g) + 3-axis gyro (deg/s)."""
    unsafe = _force_anomaly["gyro"]
    if unsafe:
        scenario = random.choice(GYRO_ANOMALIES)
        payload = {
            "sensor_id": "mpu-6050-01",
            "sensor_type": "gyro",
            "ax": round(random.uniform(*scenario["ax"]), 4),
            "ay": round(random.uniform(*scenario["ay"]), 4),
            "az": round(random.uniform(*scenario["az"]), 4),
            "gx": round(random.uniform(*scenario["gx"]), 2),
            "gy": round(random.uniform(*scenario["gy"]), 2),
            "gz": round(random.uniform(*scenario["gz"]), 2),
            "status": "unsafe",
            "reason": scenario["reason"],
        }
        label = f"  UNSAFE  gyro: {scenario['name']}"
    else:
        payload = {
            "sensor_id": "mpu-6050-01",
            "sensor_type": "gyro",
            "ax": round(random.gauss(0.0, 0.05), 4),
            "ay": round(random.gauss(0.0, 0.05), 4),
            "az": round(random.gauss(9.81, 0.08), 4),
            "gx": round(random.gauss(0.0, 0.8), 2),
            "gy": round(random.gauss(0.0, 0.8), 2),
            "gz": round(random.gauss(0.0, 0.8), 2),
            "status": "safe",
            "reason": "Normal orientation and motion — readings within expected range",
        }
        label = "  safe    gyro: normal"

    return _event(payload), label


def sound_event() -> dict:
    """HW-485 Big Sound: binary trigger."""
    triggered = _force_anomaly["sound"]
    if triggered:
        reason = random.choice(SOUND_ANOMALIES)
        payload = {
            "sensor_id": "hw485-01",
            "sensor_type": "sound",
            "triggered": True,
            "status": "unsafe",
            "reason": reason,
        }
        label = "  UNSAFE  sound: triggered"
    else:
        payload = {
            "sensor_id": "hw485-01",
            "sensor_type": "sound",
            "triggered": False,
            "status": "safe",
            "reason": "Ambient noise within normal threshold",
        }
        label = "  safe    sound: idle"

    return _event(payload), label


def magnetic_event() -> dict:
    """HW-509 Magnetic: binary trigger."""
    triggered = _force_anomaly["magnetic"]
    if triggered:
        reason = random.choice(MAGNETIC_ANOMALIES)
        payload = {
            "sensor_id": "hw509-01",
            "sensor_type": "magnetic",
            "triggered": True,
            "status": "unsafe",
            "reason": reason,
        }
        label = "  UNSAFE  magnetic: triggered"
    else:
        payload = {
            "sensor_id": "hw509-01",
            "sensor_type": "magnetic",
            "triggered": False,
            "status": "safe",
            "reason": "Magnetic field stable — enclosure sealed",
        }
        label = "  safe    magnetic: idle"

    return _event(payload), label


def _event(payload: dict) -> dict:
    return {
        "event_type": "sensor",
        "machine_id": machine_id,
        "user": USER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "sensor",
        "payload": payload,
    }


# ── Network ──────────────────────────────────────────────

def send_batch(events: list[dict], labels: list[str], url: str, api_key: str | None) -> None:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        r = requests.post(url, json=events, headers=headers, timeout=5)
        body = r.json()
        print(f"[{ts}] Sent {len(events)} events → {body.get('message', r.status_code)}")
        for lbl in labels:
            print(f"         {lbl}")
    except Exception as e:
        print(f"[{ts}] Error: {e}")


# ── Main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Simulate IoT sensor data")
    parser.add_argument("--url", default=API_URL, help="Engine events endpoint")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between batches")
    parser.add_argument("--machine-id", default=None, help="Machine ID (default: random UUID)")
    parser.add_argument("--api-key", default=None, help="Bearer token if auth is enabled")
    args = parser.parse_args()

    global machine_id
    if args.machine_id:
        machine_id = args.machine_id
    # else keeps the random UUID generated at import time

    print("Sensor simulator started")
    print(f"  Machine ID : {machine_id}")
    print(f"  Endpoint   : {args.url}")
    print(f"  Interval   : {args.interval}s")
    print("  Hotkeys    : G = gyro  |  S = sound  |  M = magnetic  (toggle anomaly)")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            results = [gyro_event(), sound_event(), magnetic_event()]
            events = [r[0] for r in results]
            labels = [r[1] for r in results]
            sensor_keys = ["gyro", "sound", "magnetic"]
            labels = [
                lbl + " \033[31m[FORCED]\033[0m" if _force_anomaly[sk] else lbl
                for lbl, sk in zip(labels, sensor_keys)
            ]
            send_batch(events, labels, args.url, args.api_key)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        _restore_term()
        print("\nStopped.")


if __name__ == "__main__":
    main()
