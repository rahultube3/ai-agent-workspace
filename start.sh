#!/bin/bash

PID_FILE=".server.pid"

if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "Server is already running (PID $(cat $PID_FILE))"
  exit 1
fi

echo "Starting Payment RAG server..."
python3 -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 &
echo $! > "$PID_FILE"

sleep 2
echo "Server started (PID $(cat $PID_FILE))"
echo "Open: http://127.0.0.1:8000"
