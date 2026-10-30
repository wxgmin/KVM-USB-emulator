# Device Pico diagnostics

This is CircuitPython code for the existing device-side Raspberry Pi Pico W.
It is not a UF2 firmware image. No extra libraries are required. It keeps the
existing GP0/GP1 UART at 460800 baud and the current keyboard/mouse interfaces.
It does not change boot.py or USB identity.

## Install
1. Plug the computer-facing DEVICE Pico into your computer normally (do not hold BOOTSEL).
2. Open its CIRCUITPY drive. Copy the existing code.py somewhere on your computer as a backup.
3. Download code.py from this branch using GitHub's Download raw file button.
   Save it as code.py, not code.py.txt, in the root of CIRCUITPY, replacing the old code.py.
4. Wait for the copy to finish, then safely eject the drive before unplugging.
   Replug the Pico once to start the new program. Existing boot.py disables auto-reload.
5. Keep boot.py and the host-side Pico unchanged.

If there is no CIRCUITPY drive, stop and report what drive appears. Do not
reflash or format it.

## Capture a failure
Open the device Pico's USB serial console on the same computer using your
existing CircuitPython serial terminal (115200 baud is suitable).
Connect without sending Ctrl-C, running a script, or resetting the board:
those actions stop or replace the running forwarding loop.
If using Thonny, its backend may interrupt code on connect; use a plain serial
terminal or restart with Ctrl-D once before testing, then leave the program running.
Console visibility depends on the current USB CDC configuration; report if no port appears.

Every 3 seconds, the program attempts a nonblocking status line. Counts are cumulative.
No keycodes, typed text, or mouse coordinates are printed or saved.
No log file is written to flash. Logging can slightly affect timing.
Capture a line while working, switch away/back until it fails, then keep pressing
a harmless key or moving the mouse and capture several more lines WITHOUT unplugging.
Age is time since last valid UART frame; an idle keyboard alone is not a fault.

- rx: UART bytes received.
- valid: checksum-valid recognized frames.
- sent: HID send calls completed (not proof the OS/application consumed the report).
- usb_err / errno: failed HID send calls and last error code.
- crc_bad: XOR-checksum failures (the protocol uses XOR, not a CRC).
- len_bad / type_bad: invalid header fields.
- unusual_len: accepted frames whose lengths differ from keyboard=8 / mouse=4.
  Existing padding/truncation behavior is retained.
- uart_err: UART read errors.
- partial_timeout: partial frames discarded after a 250 ms gap.
- kb / ms: expected HID interfaces found at program start.

Interpret changes between lines while actively providing input:
- rx stops increasing: check host-side enumeration/forwarding, UART, and power.
- rx increases but valid does not: framing/protocol corruption or unexpected sender data.
- valid and usb_err increase: device USB send path is failing.
- valid and sent increase but OS gets no input: investigate reports, descriptors and host USB.
- no diagnostic lines: ambiguous; check serial connection and whether code is running.

This build adds partial-frame recovery but does not claim to fix the intermittent failure.
It does not reset USB, retry mouse deltas, add a new heartbeat protocol, or release held keys
merely because input is idle. Host firmware is still needed for coordinated recovery.

## Roll back
Replace CIRCUITPY/code.py with your saved original, finish the copy, safely eject
and replug once. No boot.py change or firmware reflash is needed.

## Validation
Python syntax and mocked CircuitPython tests passed for fragmented UART frames,
keyboard/mouse forwarding, bad checksum recovery, USB error counters, partial-frame
timeout and diagnostic output. Physical Pico, USB timing and KVM switching remain untested.
