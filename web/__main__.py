"""Entry point: python -m web [--port 5001] [--outputs /path/to/outputs]."""

from __future__ import annotations

import argparse

from .app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Dashboard")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--outputs",
        default=None,
        help="Path to outputs/ directory (default: auto-detect from repo root)",
    )
    args = parser.parse_args()
    app = create_app(outputs_dir=args.outputs)
    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
