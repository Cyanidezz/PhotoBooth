from __future__ import annotations

import argparse

import uvicorn


parser = argparse.ArgumentParser(description="PhotoBooth Camera Server")
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--cert")
parser.add_argument("--key")
args = parser.parse_args()

uvicorn.run("server.app:app", host=args.host, port=args.port, ssl_certfile=args.cert, ssl_keyfile=args.key)

