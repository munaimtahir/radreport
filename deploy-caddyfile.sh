#!/bin/bash
# Helper script to deploy Caddyfile with sudo permissions
# Usage: ./deploy-caddyfile.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CADDYFILE_SOURCE="${SCRIPT_DIR}/Caddyfile"
CADDYFILE_DEST="/etc/caddy/Caddyfile"

if [ ! -f "$CADDYFILE_SOURCE" ]; then
    echo "Error: Caddyfile not found at $CADDYFILE_SOURCE"
    exit 1
fi

echo "Deploying Caddyfile to $CADDYFILE_DEST..."
sudo cp "$CADDYFILE_SOURCE" "$CADDYFILE_DEST"
sudo chown root:root "$CADDYFILE_DEST"
sudo chmod 644 "$CADDYFILE_DEST"

echo "Caddyfile deployed successfully!"
echo "Testing Caddyfile configuration..."
sudo caddy validate --config "$CADDYFILE_DEST" && echo "✓ Configuration is valid" || echo "✗ Configuration has errors"

echo ""
echo "To reload Caddy with the new configuration, run:"
echo "  sudo systemctl reload caddy"
echo "or"
echo "  sudo caddy reload --config $CADDYFILE_DEST"
