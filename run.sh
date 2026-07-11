#!/bin/bash
# Startup script for Lambda Web Adapter
# This launches the FastMCP server in streamable-http mode on port 8000.
# The Lambda Web Adapter extension forwards API Gateway requests to this process.

exec python server.py
