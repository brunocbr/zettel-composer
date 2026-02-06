import struct
import re
import yaml
import asyncio
import logging
import socket
import os
import sys
from typing import Optional, Tuple
from time import time

# ============================================================
# CONFIGURATION
# ============================================================
SERVICE_UUID   = "0000fff0-0000-1000-8000-00805f9b34fb"
CHAR_SYNC_UUID = "0000fff8-0000-1000-8000-00805f9b34fb"

# Configurações da Bridge (ajuste se necessário)
DEFAULT_BRIDGE_IP = "127.0.0.1"
DEFAULT_BRIDGE_PORT = 1234

log = logging.getLogger("writers_gadget")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ============================================================
# TEXT PROCESSING UTILITIES
# ============================================================

def _split_yaml_header(buffer: str) -> Tuple[Optional[dict], str]:
    lines = buffer.splitlines()
    line = None

    if not lines or lines[0].strip() != "---":
        return None, buffer

    yaml_lines = []

    for i in range(1, len(lines)):
        if lines[i].strip() in  ("---", "..."):
            body_start = i + 1
            break

        line = lines[i].replace("\t", " ")
        line = line.rstrip()

        yaml_lines.append(line)
    else:
        return None, buffer

    metadata = yaml.safe_load("\n".join(yaml_lines)) or {}
    body = "\n".join(lines[body_start:])
    return metadata, body


def _get_clean_word_count(text: str) -> int:
    lines = text.splitlines()
    output, skip_level = [], None
    for line in lines:
        m = re.match(r"^(\s*)(#+)\s+(.*)", line)
        if m:
            level = len(m.group(2))
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if "{.noexport}" in m.group(3):
                skip_level = level
                continue
        if skip_level is None and not re.match(r"^\s*#+\s+", line):
            output.append(line)
    clean_text = "\n".join(output)
    return len(re.findall(r"\b\w+\b", clean_text, flags=re.UNICODE))

# ============================================================
# SEND STRATEGIES
# ============================================================

async def _send_via_bleak(payload: bytes, mac: Optional[str] = None):
    """Native BLE sync for MacOS/Linux/Windows."""
    from bleak import BleakScanner, BleakClient

    if mac:
        log.info(f"BLE Mode: Targeting MAC {mac}")
        device = await BleakScanner.find_device_by_address(mac, timeout=5.0)
    else:
        log.info("BLE Mode: Scanning for any Writer's Gadget...")
        device = await BleakScanner.find_device_by_filter(
            lambda d, ad: SERVICE_UUID.lower() in [u.lower() for u in (ad.service_uuids or [])]
        )

    if not device:
        raise RuntimeError("Device not found via BLE scan.")

    async with BleakClient(device) as client:
        await client.write_gatt_char(CHAR_SYNC_UUID, payload, response=True)
        log.info(f"Synced via Native BLE to {device.address}")

def _send_via_tcp_bridge(payload: bytes, host: str, port: int):
    """TCP Bridge sync for Android/Termux."""
    log.info(f"Bridge Mode: Connecting to {host}:{port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect((host, port))
        s.sendall(payload)
        log.info("Synced via TCP Bridge")

# ============================================================
# PUBLIC API
# ============================================================

def wg_send_markdown_buffer(buffer: str, destination: Optional[str] = None) -> bool:
    """
    destination can be a MAC (XX:XX...), an IP (127.0.0.1), or None.
    """
    try:
        metadata, body = _split_yaml_header(buffer)

        if not metadata or "target_words" not in metadata:
            log.warning("Field 'target_words' is missing from the YAML header")
            target_words = 0
        else:
            target_words = int(metadata["target_words"])

        word_count = _get_clean_word_count(body)

        # 12-byte payload: Goal (I), Count (I), Epoch (I)
        payload = struct.pack("<III", target_words, word_count, int(time()))

        # Decidir estratégia
        is_ip = destination and re.match(r"^\d{1,3}(\.\d{1,3}){3}$", destination)

        if is_ip or "com.termux" in os.environ.get("PREFIX", ""):
            # Força Bridge no Termux ou se um IP for passado
            host = destination if is_ip else DEFAULT_BRIDGE_IP
            _send_via_tcp_bridge(payload, host, DEFAULT_BRIDGE_PORT)
        else:
            # Tenta Bleak (Desktop)
            asyncio.run(_send_via_bleak(payload, destination))

        return True
    except Exception as e:
        log.error(f"Sync failed: {e}")
        return False

if __name__ == "__main__":
    # Usage: cat note.md | python3 writers_gadget_ble.py [MAC or IP]
    dest = sys.argv[1] if len(sys.argv) > 1 else None
    stdin_data = sys.stdin.read()
    if stdin_data:
        wg_send_markdown_buffer(stdin_data, dest)
