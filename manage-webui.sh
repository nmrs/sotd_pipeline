#!/bin/bash

# SOTD Pipeline WebUI Server Manager Wrapper
# This script provides easy access to the webui server management from the project root

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBUI_SCRIPT="$SCRIPT_DIR/webui/scripts/manage-servers.sh"

if [[ ! -f "$WEBUI_SCRIPT" ]]; then
    echo "Error: WebUI server management script not found at $WEBUI_SCRIPT"
    exit 1
fi

# Pass all arguments to the webui script
exec "$WEBUI_SCRIPT" "$@" 