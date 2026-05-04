#!/bin/bash

# YourBestPath Fiduciary Engine - Automated Rebalance Wrapper
# This script is intended to be run via cron (e.g., every Monday at 9:00 AM IST)

PROJECT_DIR="/Users/shilpadhall/agentic_ai_projects/quant_agent"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/rebalance_$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

echo "--- Rebalance Cycle Started: $(date) ---" >> "$LOG_FILE"

cd "$PROJECT_DIR" || exit

# Activate Virtual Environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.

# Load API Keys if not in environment (optional, assuming they are in .env)
# source .env

# Run the Rebalance Script
./venv/bin/python3 scripts/run_one_time_rebalance.py >> "$LOG_FILE" 2>&1

echo "--- Rebalance Cycle Completed: $(date) ---" >> "$LOG_FILE"
