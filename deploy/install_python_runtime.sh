#!/usr/bin/env bash
set -euo pipefail

# Run as the stockbot Linux user from the project root after the repository is cloned.
python3 -m venv .venv
.venv/bin/python3 -m pip install --upgrade pip
.venv/bin/python3 -m pip install .
echo "Python runtime installed. Configure /etc/stockbot-tse.env before starting the service."
