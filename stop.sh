#!/bin/bash

PID_FILE=".server.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "No running server found."
  exit 1
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  rm "$PID_FILE"
  echo "Server stopped (PID $PID)"
else
  echo "Server was not running. Cleaning up..."
  rm "$PID_FILE"
fi
