"""Render the frozen, label-blind notebook packet as local Markdown."""

import argparse
from pathlib import Path

from researchproof.blind_review import readable_packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--expected-packet-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; use a new path to preserve prior packets")
    try:
        document = readable_packet(args.packet, args.expected_packet_sha256)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8")
    print(f"Wrote a label-blind local packet to {args.output}")


if __name__ == "__main__":
    main()
