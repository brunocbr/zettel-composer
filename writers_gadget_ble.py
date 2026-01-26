import struct
import re
import yaml
import asyncio
import logging
from typing import Optional, Tuple
from time import sleep

from bleak import BleakScanner, BleakClient


# ============================================================
# CONFIGURATION (ADJUST ONLY IF NECESSARY)
# ============================================================

# DEVICE_NAME = "Writers' Gadget"
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHAR_TARGET_UUID = "0000fff2-0000-1000-8000-00805f9b34fb"
CHAR_COUNT_UUID  = "0000fff1-0000-1000-8000-00805f9b34fb"

YAML_START = "---"
YAML_END = ("---", "...")

# ============================================================
# LOGGING (silent by default)
# ============================================================

log = logging.getLogger("writers_gadget_ble")
log.addHandler(logging.NullHandler())


# ============================================================
# INTERNAL UTILITIES
# ============================================================

def _u32(value: int) -> bytes:
    return struct.pack("<I", value)



def _split_yaml_header(buffer: str) -> Tuple[Optional[dict], str]:
    lines = buffer.splitlines()
    line = None

    if not lines or lines[0].strip() != YAML_START:
        return None, buffer

    yaml_lines = []

    for i in range(1, len(lines)):
        if lines[i].strip() in YAML_END:
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


def _strip_markdown_headings(text: str) -> str:
    kept_lines = []
    for line in text.splitlines():
        if re.match(r"^\s*#+\s+", line):
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


async def _find_device(timeout: float = 5.0) -> str:
    # devices = await BleakScanner.discover(timeout=timeout)
    #
    # for d in devices:
    #     if d.name == DEVICE_NAME:
    #         return d

    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: SERVICE_UUID.lower() in [u.lower() for u in (ad.service_uuids or [])],
        timeout=timeout,
    )

    if device is None:
        raise RuntimeError("BLE device advertising the expected service was not found")
    else:
        return device


async def _send_ble(word_count: int, target_words: int):
    device = await _find_device()

    async with BleakClient(device) as client:
        if not client.is_connected:
            raise RuntimeError("Failed to connect to the BLE gadget")

        await client.write_gatt_char(
            CHAR_TARGET_UUID,
            struct.pack("<I", target_words),
            response=False
        )

        await client.write_gatt_char(
            CHAR_COUNT_UUID,
            struct.pack("<I", word_count),
            response=False
        )

        sleep(1)  # ridiculous but needed


def _run_async(coro):
    """
    Safely execute a coroutine:
    - creates an event loop if none exists
    - schedules a task if a loop is already running
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coro)
    else:
        loop.create_task(coro)

def _strip_noexport_sections(text: str) -> str:
    """
    Removes sections whose heading ends with '{.noexport}'.
    The section includes the heading itself and all content
    until a heading of the same or higher level appears.
    """
    output = []
    skip_level = None

    for line in text.splitlines():
        m = re.match(r"^(\s*)(#+)\s+(.*)", line)

        if m:
            level = len(m.group(2))
            title = m.group(3).rstrip()

            # End skipping if we reached same or higher level
            if skip_level is not None and level <= skip_level:
                skip_level = None

            # Start skipping if this heading has {.noexport}
            if title.endswith("{.noexport}"):
                skip_level = level
                continue

        if skip_level is None:
            output.append(line)

    return "\n".join(output)

# ============================================================
# PUBLIC API
# ============================================================

def wg_send_markdown_buffer(buffer: str) -> bool:
    """
    Safe public API (best-effort).

    - Never raises exceptions
    - Parses Markdown + YAML
    - Counts words
    - Sends data via BLE (two characteristics)
    - Returns True on success, False on failure
    """
    try:
        metadata, body = _split_yaml_header(buffer)

        if not metadata or "target_words" not in metadata:
            log.warning("Field 'target_words' is missing from the YAML header")
            target_words = 0
        else:
            target_words = int(metadata["target_words"])

        body = _strip_noexport_sections(body)
        body = _strip_markdown_headings(body)

        word_count = _word_count(body)
        target_words = target_words

        _run_async(_send_ble(word_count, target_words))
        return True

    except Exception:
        log.exception("Error while processing or sending data to the Writer’s Gadget")
        return False
