#!/usr/bin/env bash
set -euo pipefail

# Run with sudo from the cloned project root. It never writes secrets.
install -o root -g root -m 0644 deploy/stockbot-tse.service /etc/systemd/system/stockbot-tse.service
install -o root -g root -m 0644 deploy/stockbot-telegram.service /etc/systemd/system/stockbot-telegram.service
install -o root -g root -m 0644 deploy/stockbot-bale.service /etc/systemd/system/stockbot-bale.service
systemctl daemon-reload
systemctl enable stockbot-tse.service
systemctl enable stockbot-telegram.service
systemctl enable stockbot-bale.service
echo "Services installed. Create /etc/stockbot-tse.env with mode 600 before starting either service."
