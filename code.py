"""
code.py — Device Pico v3 (Optimized)
Reads UART frames from Host Pico, sends USB HID to PC 1.
Optimized for minimum latency in CircuitPython.
"""
import board
import busio
import usb_hid
import usb_cdc
import time

uart = busio.UART(
    tx=board.GP0,
    rx=board.GP1,
    baudrate=460800,
    timeout=0,
    receiver_buffer_size=1024,
)

keyboard = None
mouse = None
for device in usb_hid.devices:
    if device.usage_page == 0x01:
        if device.usage == 0x06:
            keyboard = device
        elif device.usage == 0x02:
            mouse = device

# Pre-allocate all buffers to avoid garbage collection pauses
_read_buf = bytearray(128)
_frame_buf = bytearray(16)
_kb_report = bytearray(8)
_mouse_report = bytearray(4)

SYNC    = 0xAA
TYPE_KB = 0x4B
TYPE_MS = 0x4D

# Diagnostics: counters only, never keycodes or mouse coordinates.
# Nonblocking console prevents logging from waiting on a serial reader.
console = usb_cdc.console
if console is not None:
    console.write_timeout = 0
rx_bytes = valid = sent = usb_errors = bad_checksum = bad_length = 0
bad_type = unusual_length = uart_errors = partial_timeout = 0
last_errno = 0
last_rx = last_valid = None
last_log = time.monotonic()
PARTIAL_TIMEOUT = 0.250

# Inline state machine — no function calls for speed
state     = 0  # 0=sync 1=type 2=len 3=data 4=check
frame_type = 0
frame_len  = 0
buf_idx    = 0

while True:
    now = time.monotonic()
    # Discard an interrupted partial frame; this never releases held keys.
    if state and last_rx is not None and now - last_rx > PARTIAL_TIMEOUT:
        state = 0
        partial_timeout += 1

    if now - last_log >= 3:
        last_log = now
        if console is not None and console.connected:
            age = -1 if last_valid is None else int((now - last_valid) * 1000)
            line = (
                "diag rx=%d valid=%d sent=%d usb_err=%d errno=%s "
                "crc_bad=%d len_bad=%d type_bad=%d unusual_len=%d "
                "uart_err=%d partial_timeout=%d age_ms=%d kb=%d ms=%d\r\n"
                % (rx_bytes, valid, sent, usb_errors, last_errno,
                   bad_checksum, bad_length, bad_type, unusual_length,
                   uart_errors, partial_timeout, age,
                   keyboard is not None, mouse is not None)
            )
            try:
                console.write(line.encode("ascii"))
            except OSError:
                pass

    try:
        n = uart.readinto(_read_buf)
    except OSError:
        uart_errors += 1
        state = 0
        continue
    if n is None or n == 0:
        continue
    rx_bytes += n
    last_rx = now

    for i in range(n):
        byte = _read_buf[i]

        if state == 0:
            if byte == SYNC:
                state = 1
        elif state == 1:
            frame_type = byte
            if frame_type == TYPE_KB or frame_type == TYPE_MS:
                state = 2
            else:
                bad_type += 1
                state = 0
        elif state == 2:
            frame_len = byte
            if 0 < frame_len <= 16:
                buf_idx = 0
                state = 3
            else:
                bad_length += 1
                state = 0
        elif state == 3:
            _frame_buf[buf_idx] = byte
            buf_idx += 1
            if buf_idx >= frame_len:
                state = 4
        elif state == 4:
            expected = frame_type ^ frame_len
            for j in range(frame_len):
                expected ^= _frame_buf[j]
            if expected == byte:
                valid += 1
                last_valid = now
                if frame_len != (8 if frame_type == TYPE_KB else 4):
                    unusual_length += 1
                try:
                    if frame_type == TYPE_KB and keyboard is not None:
                        for j in range(8):
                            _kb_report[j] = _frame_buf[j] if j < frame_len else 0
                        keyboard.send_report(_kb_report)
                        sent += 1
                    elif frame_type == TYPE_MS and mouse is not None:
                        for j in range(4):
                            _mouse_report[j] = _frame_buf[j] if j < frame_len else 0
                        mouse.send_report(_mouse_report)
                        sent += 1
                except OSError as exc:
                    usb_errors += 1
                    last_errno = exc.args[0] if exc.args else 0
            else:
                bad_checksum += 1
            state = 0
