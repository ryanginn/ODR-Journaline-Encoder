#!/usr/bin/env python3
"""Feed a Journaline .dat file (packet mode) through the Fraunhofer decoder
built by build.sh and print what it decodes:  check.py file.dat [packet address]"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from odr_jml.encoder import msc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    args = sys.argv[1:]
    with open(args[0], "rb") as f:
        by_addr = msc.parse_packets(f.read())
    addr = int(args[1], 0) if len(args) > 1 else next(iter(by_addr))
    groups = by_addr[addr]
    with tempfile.NamedTemporaryFile(delete=False) as f:
        for g in groups:
            f.write(len(g).to_bytes(2, "big") + g)
    try:
        subprocess.run([os.path.join(HERE, "build", "jml-decode"), f.name], check=True)
    finally:
        os.unlink(f.name)


if __name__ == "__main__":
    main()
