from __future__ import annotations

import argparse
import sys

import uvicorn

from .app import create_app
from .config import load_config


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="lakerboat")
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="Run the RDK X3 dashboard and control service.")
    run.add_argument("--config", default="config/demo.yaml", help="YAML config path.")
    run.add_argument("--host", default=None, help="Override server host.")
    run.add_argument("--port", type=int, default=None, help="Override server port.")

    once = sub.add_parser("step", help="Run one control step for smoke testing.")
    once.add_argument("--config", default="config/demo.yaml", help="YAML config path.")

    args = parser.parse_args(argv)
    if args.command in (None, "run"):
        config = load_config(getattr(args, "config", "config/demo.yaml"))
        if getattr(args, "host", None):
            config.server.host = args.host
        if getattr(args, "port", None):
            config.server.port = args.port
        app = create_app(config)
        uvicorn.run(app, host=config.server.host, port=config.server.port)
        return

    if args.command == "step":
        from .runtime import BoatRuntime

        runtime = BoatRuntime(load_config(args.config))
        runtime.step()
        print(runtime.get_status())
        runtime.stop()
        return

    parser.print_help()
    sys.exit(2)
