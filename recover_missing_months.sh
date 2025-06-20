#!/bin/bash

# Missing Months Data Recovery Script
# This script fetches all the missing months identified in the recovery plan

echo "Starting missing months data recovery..."
echo "========================================"

# List of missing months to recover
MISSING_MONTHS=(
    "2017-08"  # August 2017
    "2018-05"  # May 2018
    "2018-08"  # August 2018
    "2019-05"  # May 2019
    "2019-08"  # August 2019
    "2022-05"  # May 2022
)

# Counter for progress tracking
TOTAL=${#MISSING_MONTHS[@]}
CURRENT=0

for month in "${MISSING_MONTHS[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo "[$CURRENT/$TOTAL] Fetching $month..."
    
    # Run fetch with force flag
    python -m sotd.fetch.run --force --month "$month"
    
    # Check if fetch was successful
    if [ $? -eq 0 ]; then
        echo "✅ Successfully fetched $month"
    else
        echo "❌ Failed to fetch $month"
    fi
    
    echo "----------------------------------------"
done

echo "Data recovery complete!"
echo "========================================"

# Show final status
echo "Final thread count:"
find data/threads -name "*.json" | wc -l

echo "Final comment count:"
find data/comments -name "*.json" | wc -l 