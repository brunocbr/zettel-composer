import struct
import re
import yaml
import asyncio
import logging
import subprocess
import os
import sys
from typing import Optional, Tuple
from time import time, sleep

# ============================================================
# CONDITIONAL IMPORTS & BACKEND DETECTION
# ============================================================
try:
    from bleak import BleakScanner, BleakClient
    HAS_BLEAK = True
except ImportError:
    HAS_BLEAK = False

def _is_termux() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "")

# ============================================================
# CONFIGURATION
# ============================================================
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHAR_TARGET_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
CHAR_COUNT_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
CHAR_DATETIME_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"

YAML_START = "---"
YAML_END = ("---", "...")

log = logging.getLogger("writers_gadget_ble")
# Set level to INFO to see success messages, or WARNING to stay silent
logging.basicConfig(level=logging.INFO)

# ============================================================
# TEXT PROCESSING UTILITIES
# ============================================================

def _split_yaml_header(buffer: str) -> Tuple[Optional[dict], str]:
    lines = buffer.splitlines()
    if not lines or lines[0].strip() != YAML_START:
        return None, buffer

    yaml_lines = []
    body_start = 0
    for i in range(1, len(lines)):
        if lines[i].strip() in YAML_END:
            body_start = i + 1
            break
        yaml_lines.append(lines[i].replace("\t", " ").rstrip())
    else:
        return None, buffer

    metadata = yaml.safe_load("\n".join(yaml_lines)) or {}
    return metadata, "\n".join(lines[body_start:])

def _strip_noexport_sections(text: str) -> str:
    output = []
    skip_level = None
    for line in text.splitlines():
        m = re.match(r"^(\s*)(#+)\s+(.*)", line)
        if m:
            level = len(m.group(2))
            title = m.group(3).rstrip()
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if title.endswith("{.noexport}"):
                skip_level = level
                continue
        if skip_level is None:
            output.append(line)
    return "\n".join(output)

def _strip_markdown_headings(text: str) -> str:
    kept_lines = []
    for line in text.splitlines():
        if re.match(r"^\s*#+\s+", line):
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)

def _word_count(text: str) -> int:
    # Basic word count ignoring symbols
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))

# ============================================================
# BLE BACKENDS
# ============================================================

async def _send_ble_desktop(word_count: int, target_words: int):
    """Backend for MacOS/Linux using Bleak library."""
    log.info("Attempting to find device via Bleak...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: SERVICE_UUID.lower() in [u.lower() for u in (ad.service_uuids or [])],
        timeout=5.0
    )

    if device is None:
        raise RuntimeError("Writer's Gadget device not found")

    async with BleakClient(device) as client:
        await client.write_gatt_char(CHAR_TARGET_UUID, struct.pack("<I", target_words))
        await client.write_gatt_char(CHAR_COUNT_UUID, struct.pack("<I", word_count))
        # Send current Epoch for RTC sync
        await client.write_gatt_char(CHAR_DATETIME_UUID, struct.pack("<I", int(time())))
        log.info(f"Sync complete: {word_count}/{target_words} words.")
        sleep(0.5)

def _send_ble_termux(word_count: int, target_words: int, mac: str):
    """Backend for Android using Termux:API commands."""
    if not mac:
        log.error("DEVICE_MAC is required when running on Termux/Android")
        return

    def gatt_write(uuid, data_bytes):
        hex_val = data_bytes.hex()
        cmd = ["termux-ble-gatt-write", "-d", mac, "-u", uuid, "-v", hex_val]
        subprocess.run(cmd, check=True, capture_output=True)

    try:
        log.info(f"Sending data to {mac} via Termux:API...")
        gatt_write(CHAR_TARGET_UUID, struct.pack("<I", target_words))
        gatt_write(CHAR_COUNT_UUID, struct.pack("<I", word_count))
        gatt_write(CHAR_DATETIME_UUID, struct.pack("<I", int(time())))
        log.info(f"Successfully sent to {mac}: {word_count}/{target_words}")
    except subprocess.CalledProcessError as e:
        log.error(f"Termux BLE write failed. Is Bluetooth ON? Error: {e.stderr.decode()}")
    except Exception as e:
        log.error(f"Unexpected error in Termux backend: {e}")

# ============================================================
# PUBLIC API
# ============================================================

def wg_send_markdown_buffer(buffer: str, device_mac: str = None) -> bool:
    """
    Main entry point for syncing.
    Detects platform and chooses appropriate BLE backend.
    """
    try:
        # 1. Parse Metadata and Body
        metadata, body = _split_yaml_header(buffer)

        # 2. Extract Target
        if not metadata or "target_words" not in metadata:
            log.warning("Field 'target_words' is missing from YAML header. Using 0.")
            target_words = 0
        else:
            target_words = int(metadata["target_words"])

        # 3. Clean and Count Words
        body = _strip_noexport_sections(body)
        body = _strip_markdown_headings(body)
        word_count = _word_count(body)

        # 4. Dispatch to correct backend
        if _is_termux():
            _send_ble_termux(word_count, target_words, device_mac)
        elif HAS_BLEAK:
            asyncio.run(_send_ble_desktop(word_count, target_words))
        else:
            log.error("No compatible Bluetooth backend found. Install 'bleak' or 'termux-api'.")
            return False

        return True

    except Exception as e:
        log.exception(f"Fatal error in wg_send_markdown_buffer: {e}")
        return False

if __name__ == "__main__":
    # Allows testing via CLI: 
    # cat file.md | python3 writers_gadget_ble.py XX:XX:XX:XX:XX:XX
    mac_input = sys.argv[1] if len(sys.argv) > 1 else None
    stdin_data = sys.stdin.read()
    if stdin_data:
        wg_send_markdown_buffer(stdin_data, mac_input)
