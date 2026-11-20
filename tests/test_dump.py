#!/usr/bin/env python3
"""Compare nasmhex output to tests/golden.txt.

Order:
  1. Python oracle of samples/hello.bin must match golden.txt
  2. docker run --rm nasmhex, if Docker is up
  3. ./nasmhex on a Linux host, if the binary exists

No assembler required on the host. Exit 0 on pass.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "hello.bin"
GOLDEN = ROOT / "tests" / "golden.txt"


def hexdump_c(data: bytes) -> str:
    """GNU hexdump -C line format (8-digit offset, 16-byte rows, final size)."""
    lines: list[str] = []
    offset = 0
    n = len(data)
    while offset < n:
        chunk = data[offset : offset + 16]
        parts = [f"{offset:08x}  "]
        for i in range(16):
            if i == 8:
                parts.append(" ")
            if i < len(chunk):
                parts.append(f"{chunk[i]:02x} ")
            else:
                parts.append("   ")
        parts.append(" |")
        for b in chunk:
            parts.append(chr(b) if 0x20 <= b <= 0x7E else ".")
        parts.append("|\n")
        lines.append("".join(parts))
        offset += len(chunk)
    lines.append(f"{offset:08x}\n")
    return "".join(lines)


def load_golden() -> str:
    return GOLDEN.read_text(encoding="ascii")


def fail(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.exit(1)


def try_docker() -> str | None:
    try:
        probe = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=12,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if probe.returncode != 0:
        return None
    run = subprocess.run(
        ["docker", "run", "--rm", "nasmhex"],
        capture_output=True,
        timeout=60,
    )
    if run.returncode != 0:
        build = subprocess.run(
            ["docker", "build", "-t", "nasmhex", str(ROOT)],
            capture_output=True,
            timeout=180,
        )
        if build.returncode != 0:
            sys.stderr.write(build.stderr.decode("utf-8", "replace"))
            fail("docker build failed")
        run = subprocess.run(
            ["docker", "run", "--rm", "nasmhex"],
            capture_output=True,
            timeout=60,
        )
    if run.returncode != 0:
        sys.stderr.write(run.stderr.decode("utf-8", "replace"))
        fail("docker run nasmhex exited %d" % run.returncode)
    return run.stdout.decode("ascii")


def try_host_binary() -> str | None:
    exe = ROOT / "nasmhex"
    if not exe.is_file():
        return None
    run = subprocess.run(
        [str(exe), str(SAMPLE)],
        capture_output=True,
        timeout=10,
    )
    if run.returncode != 0:
        sys.stderr.write(run.stderr.decode("utf-8", "replace"))
        fail("host nasmhex exited %d" % run.returncode)
    return run.stdout.decode("ascii")


def main() -> None:
    if not SAMPLE.is_file():
        fail("missing %s" % SAMPLE)
    got_oracle = hexdump_c(SAMPLE.read_bytes())
    if not GOLDEN.is_file():
        GOLDEN.write_text(got_oracle, encoding="ascii")
        sys.stderr.write("wrote %s\n" % GOLDEN)

    golden = load_golden()
    if got_oracle != golden:
        fail("oracle(samples/hello.bin) != tests/golden.txt")

    docker_out = try_docker()
    if docker_out is not None:
        if docker_out != golden:
            fail("docker run output != tests/golden.txt")
        print("ok  docker run --rm nasmhex")
    else:
        print("skip docker (not available)")

    host_out = try_host_binary()
    if host_out is not None:
        if host_out != golden:
            fail("./nasmhex output != tests/golden.txt")
        print("ok  ./nasmhex samples/hello.bin")
    else:
        print("skip host binary (not built)")

    print("ok  golden (%d bytes, %d lines)" % (len(golden), golden.count("\n")))
    sys.exit(0)


if __name__ == "__main__":
    main()
