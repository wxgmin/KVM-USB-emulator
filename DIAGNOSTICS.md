# Device Pico diagnostics

This is CircuitPython code for the existing device-side Raspberry Pi Pico W.
It is not a UF2 firmware image. No extra libraries are required. It keeps the
existing GP0/GP1 UART at 460800 baud and the current keyboard/mouse interfaces.
It does not change boot.py or USB identity.

## Install
1. Plug the computer-facing DEVICE Pico into your computer normally (do not hold BOOTSEL).
2. Identify its CIRCUITPY drive and USB serial port. Back up all existing files to a
   folder on your computer, including code.py and boot.py, and verify the copies.
   Keep the backup outside CIRCUITPY.
3. Download code.py from this branch using GitHub's Download raw file button.
   Save it as code.py, not code.py.txt, in the root of CIRCUITPY, replacing the old code.py.
4. Wait for the copy to finish and verify it. Existing boot.py disables auto-reload.
   To start the diagnostic code while preserving the laptop USB connection, open a
   plain serial console and press Ctrl-C to stop the old loop. CircuitPython may
   display "Press any key to enter the REPL"; press Ctrl-C again to reach `>>>`.
   At `>>>`, press Ctrl-D once to soft-reload code.py. This briefly interrupts
   forwarding. Do this only for setup, before the baseline capture.
   Confirm diagnostic lines appear; do not unplug or hard-reset the board.
5. Keep boot.py and the host-side Pico unchanged.

If there is no CIRCUITPY drive, stop and report what drive appears. Do not
reflash or format it. If Windows reports write-protected media, stop the file
installation and keep the original files. Do not clear disk attributes, disable
write protection, or alter boot.py as a routine diagnostic step. A controlled
serial session can run the diagnostic code temporarily in RAM without writing
flash; that is a temporary test, not a persistent installation. A reload returns
to the saved code.py. Never interrupt a live failure capture to load or reload code.

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
Replace CIRCUITPY/code.py with your saved original, finish and verify the copy,
then use the one-time Ctrl-C / REPL / Ctrl-D setup sequence above. No boot.py
change, USB unplug, or firmware reflash is needed. If testing only in RAM, the
original code.py is already unchanged; one soft reload restores it. Stop log
capture before rollback. Do not roll back until the failure evidence is saved.

## Validation
Python syntax and mocked CircuitPython tests passed for fragmented UART frames,
keyboard/mouse forwarding, bad checksum recovery, USB error counters, partial-frame
timeout and diagnostic output.

On 2026-10-30, a Pico W running CircuitPython 10.1.4 was identified through its
CIRCUITPY boot information and matching USB serial identity. All existing files
were backed up and hash-verified. Windows reported CIRCUITPY read-only, so the
diagnostic code was run temporarily in RAM through USB CDC. Both HID interfaces
were found, and initial UART frames completed HID send calls with zero USB send
errors. A soft reload returned to the original code without unplugging USB.
The user then reported that keyboard and mouse worked after the requested KVM
switch-away/back test. The capture reached 1,642 valid frames and 1,642 completed
HID send calls, with zero USB, UART, checksum, header, or partial-timeout errors.
No failure was reproduced in this test. Completed send calls alone do not prove
OS/application input consumption. Intermittent failure reproduction, recovery,
long-term timing, and persistent installation remain pending.
