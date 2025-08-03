#!/bin/bash
# Auto-sync CrewAI documentation

# Configuration
DOCS_DIR="/Users/hretheum/dev/bezrobocie/vector-wave/knowledge-base/data/crewai-docs"
LOG_FILE="/Users/hretheum/dev/bezrobocie/vector-wave/knowledge-base/logs/sync.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Function to sync documentation
sync_docs() {
    log "Starting CrewAI documentation sync..."
    
    cd "$DOCS_DIR" || {
        log "ERROR: Cannot change to docs directory: $DOCS_DIR"
        exit 1
    }
    
    # Fetch latest changes
    log "Fetching latest changes from CrewAI repository..."
    git fetch origin main
    
    # Check if there are updates
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log "Documentation is up to date. No sync needed."
        return 0
    fi
    
    # Pull latest changes
    log "Pulling latest documentation..."
    git pull origin main
    
    if [ $? -eq 0 ]; then
        log "Successfully synced documentation"
        
        # Trigger knowledge base update (if needed)
        # python3 /path/to/update_kb.py
        
        # Record last sync
        echo "$TIMESTAMP" > "$DOCS_DIR/.last_sync"
    else
        log "ERROR: Failed to pull latest documentation"
        return 1
    fi
}

# Main execution
main() {
    log "=== CrewAI Documentation Sync Script ==="
    
    # Check if docs directory exists
    if [ ! -d "$DOCS_DIR" ]; then
        log "ERROR: Documentation directory not found: $DOCS_DIR"
        exit 1
    fi
    
    # Run sync
    sync_docs
    
    log "Sync process completed"
}

# Run main function
main