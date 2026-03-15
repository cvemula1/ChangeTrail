# Copyright (c) 2026 cvemula1
# Licensed under the MIT License. See LICENSE file in the project root.
# https://github.com/cvemula1/ChangeTrail

"""
CLI entry point.

    changetrail serve       Start the API server
    changetrail demo        Print a demo incident timeline (no deps needed)
    changetrail seed        Seed demo events into the database
    changetrail version     Print version and exit
"""

import argparse
import asyncio
import logging
import sys

from changetrail import __version__


def main():
    p = argparse.ArgumentParser(
        prog="changetrail",
        description="What changed before this alert?",
    )
    sub = p.add_subparsers(dest="command")

    sv = sub.add_parser("serve", help="Start the API server")
    sv.add_argument("--host", default="0.0.0.0")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--reload", action="store_true")

    sub.add_parser("demo", help="Print a demo incident timeline")
    sub.add_parser("seed", help="Seed demo events into the database")
    sub.add_parser("version", help="Show version")

    args = p.parse_args()

    if args.command == "serve":
        _serve(args)
    elif args.command == "demo":
        _demo()
    elif args.command == "seed":
        _seed()
    elif args.command == "version":
        print(f"changetrail {__version__}")
    else:
        p.print_help()


def _serve(args):
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    uvicorn.run(
        "changetrail.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


def _demo():
    from changetrail.demo import print_demo_timeline
    print_demo_timeline()


def _seed():
    from changetrail.demo import seed_demo_events

    logging.basicConfig(level=logging.INFO)
    n = asyncio.run(seed_demo_events())
    print(f"Seeded {n} demo events.")


if __name__ == "__main__":
    main()
