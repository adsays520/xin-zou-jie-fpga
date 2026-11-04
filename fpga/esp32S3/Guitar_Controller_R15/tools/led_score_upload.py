"""Upload an LED-only cue score to S3 RAM; never sends audio or flashes firmware."""
import argparse
import csv
from pathlib import Path
import re
import time


def load_score(path):
    events = []
    with open(path, encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            event = tuple(int(row[k]) for k in ("time_ms", "position", "string", "duration_ms"))
            at, position, string, duration = event
            if not (0 <= position <= 21 and 0 <= string <= 6 and (position or string)
                    and 1 <= duration <= 3600000 and 0 <= at <= 3600000 - duration):
                raise ValueError(f"Invalid LED cue: {event}")
            events.append(event)
    if not 1 <= len(events) <= 256:
        raise ValueError("Score must contain 1..256 cues")
    return sorted(events)


def reply_payload(line):
    line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
    if "HOST_REPLY:" in line:
        line = line.split("HOST_REPLY:", 1)[1].strip()
    return line


def send(port, line):
    encoded = (line + "\n").encode("ascii")
    if port.write(encoded) != len(encoded):
        raise RuntimeError("Incomplete command write; not retrying an uncertain cue")
    port.flush()
    until = time.monotonic() + 3
    while time.monotonic() < until:
        reply = reply_payload(port.readline().decode("utf-8", errors="replace"))
        if reply == "OK,LED":
            return
        if reply.startswith("ERROR,LED") or reply in ("ERROR,USB_COMMAND", "ERROR,COMMAND"):
            raise RuntimeError(reply)
    raise TimeoutError("No LED acknowledgement; check S3 port and LED firmware")


def upload(port, events, both=False):
    send(port, "LED,STOP")
    send(port, "LED,CLEAR")
    for event in events:
        send(port, "LED,ADD," + ",".join(map(str, event)))
    send(port, "LED,MODE," + ("BOTH" if both else "GUIDE"))
    send(port, "LED,PLAY")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path)
    parser.add_argument("--port", help="S3 native USB, e.g. COM30")
    parser.add_argument("--both", action="store_true", help="Keep live touch lights during guide playback")
    parser.add_argument("--check", action="store_true", help="Validate CSV without opening any port")
    args = parser.parse_args()
    events = load_score(args.score)
    if args.check:
        print(f"OK: {len(events)} LED-only cues; positions 1..21; strings 1..6")
        return
    if not args.port:
        parser.error("Upload requires --port COMxx")
    import serial
    port = serial.Serial(port=None, baudrate=115200, timeout=.15, write_timeout=2)
    port.dtr = False
    port.rts = False
    port.port = args.port
    port.open()
    try:
        time.sleep(.3)
        port.reset_input_buffer()
        upload(port, events, args.both)
    finally:
        port.close()
    print("Uploaded LED cues. S3 runs playback locally; RAM score is lost on reset. No audio was sent.")


if __name__ == "__main__":
    main()
