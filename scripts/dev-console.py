#!/usr/bin/env python3
"""Run commands on the hanoip device over its USB CDC-ACM serial console.

The gadget exposes a getty on ttyGS0, which macOS shows as /dev/tty.usbmodem*.
This logs in as root and runs the commands given as arguments (or on stdin).

    scripts/dev-console.py 'uname -a' 'ls /dev/sd*'
    echo 'dmesg | tail' | scripts/dev-console.py
"""
import glob
import os
import select
import sys
import termios
import time

USER = os.environ.get("DEV_USER", "root")
PASS = os.environ.get("DEV_PASS", "147147")
BAUD = int(os.environ.get("DEV_BAUD", "115200"))


def find_port():
    ports = sorted(glob.glob("/dev/tty.usbmodem*") + glob.glob("/dev/tty.usbserial*"))
    if not ports:
        sys.exit("no /dev/tty.usbmodem* found (is the gadget up?)")
    return ports[0]


def open_raw(port):
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(fd)
    cc = list(cc)
    cc[termios.VMIN] = 0
    cc[termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, [
        0, 0, termios.CS8 | termios.CREAD | termios.CLOCAL, 0,
        termios.B115200, termios.B115200, cc,
    ])
    return fd


def read_for(fd, seconds, quiet=True):
    buf = b""
    end = time.time() + seconds
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try:
                d = os.read(fd, 8192)
            except OSError:
                break
            buf += d
    if not quiet:
        sys.stdout.write(buf.decode("latin1", "replace"))
        sys.stdout.flush()
    return buf


def wait_for(fd, needle, timeout=25):
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.3)
        if r:
            try:
                buf += os.read(fd, 8192)
            except OSError:
                break
            if needle in buf:
                return True, buf
    return False, buf


def main():
    cmds = sys.argv[1:]
    if not cmds:
        cmds = [ln.rstrip("\n") for ln in sys.stdin if ln.strip()]

    port = find_port()
    fd = open_raw(port)
    print(f">> {port}", file=sys.stderr)

    # Nudge the console and wait for the login prompt (retry a few times in
    # case the getty is not quite ready yet).
    logged_in = False
    for _ in range(6):
        os.write(fd, b"\r")
        ok, buf = wait_for(fd, b"login:", 5)
        if ok:
            os.write(fd, USER.encode() + b"\r")
            ok, buf = wait_for(fd, b"assword", 8)
            if ok:
                os.write(fd, PASS.encode() + b"\r")
                if wait_for(fd, b"#", 8)[0]:
                    logged_in = True
            break
        if b"#" in buf or b"$" in buf:
            logged_in = True
            break
    if not logged_in:
        print(">> warning: could not confirm login", file=sys.stderr)

    for c in cmds:
        os.write(fd, c.encode() + b"\r")
        time.sleep(0.4)
        out = read_for(fd, 3)
        sys.stdout.write(out.decode("latin1", "replace"))
    sys.stdout.write("\n")
    os.close(fd)


if __name__ == "__main__":
    main()
