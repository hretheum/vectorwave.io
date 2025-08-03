#!/bin/bash
# Setup cron job for CrewAI docs sync

SCRIPT_PATH="/Users/hretheum/dev/bezrobocie/vector-wave/knowledge-base/scripts/sync_crewai_docs.sh"
CRON_SCHEDULE="0 2 * * *"  # Daily at 2 AM

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "ERROR: Sync script not found at: $SCRIPT_PATH"
    exit 1
fi

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $SCRIPT_PATH") | crontab -

echo "Cron job added successfully!"
echo "Current crontab:"
crontab -l

echo ""
echo "To remove the cron job, run:"
echo "crontab -e"
echo "And remove the line with sync_crewai_docs.sh"