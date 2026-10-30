"""
code.py — Device Pico v3 (Optimized)
Reads UART frames from Host Pico, sends USB HID to PC 1.
Optimized for minimum latency in CircuitPython.
"""
import board
import busio
import usb_hid

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

# Inline state machine — no function calls for speed
state     = 0  # 0=sync 1=type 2=len 3=data 4=check
frame_type = 0
frame_len  = 0
buf_idx    = 0

while True:
    n = uart.readinto(_read_buf)
    if n is None or n == 0:
        continue

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
                state = 0
        elif state == 2:
            frame_len = byte
            if 0 < frame_len <= 16:
                buf_idx = 0
                state = 3
            else:
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
                try:
                    if frame_type == TYPE_KB and keyboard is not None:
                        for j in range(8):
                            _kb_report[j] = _frame_buf[j] if j < frame_len else 0
                        keyboard.send_report(_kb_report)
                    elif frame_type == TYPE_MS and mouse is not None:
                        for j in range(4):
                            _mouse_report[j] = _frame_buf[j] if j < frame_len else 0
                        mouse.send_report(_mouse_report)
                except OSError:
                    pass
            state = 0
