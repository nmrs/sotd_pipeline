#!/bin/bash

# Process Recovered Months Through Pipeline
# This script processes all recovered months through extract, match, enrich, aggregate, and report phases

echo "Processing recovered months through pipeline phases..."
echo "====================================================="

# List of recovered months to process
RECOVERED_MONTHS=(
    "2017-08"  # August 2017
    "2018-05"  # May 2018
    "2018-08"  # August 2018
    "2019-05"  # May 2019
    "2019-08"  # August 2019
    "2022-05"  # May 2022
)

# Counter for progress tracking
TOTAL=${#RECOVERED_MONTHS[@]}
CURRENT=0

for month in "${RECOVERED_MONTHS[@]}"; do
    CURRENT=$((CURRENT + 1))
    echo "[$CURRENT/$TOTAL] Processing $month through pipeline phases..."
    
    # Phase 1: Extract
    echo "  📊 Extracting data..."
    python -m sotd.extract.run --force --month "$month"
    if [ $? -ne 0 ]; then
        echo "❌ Extract failed for $month"
        continue
    fi
    
    # Phase 2: Match
    echo "  🔍 Matching products..."
    python -m sotd.match.run --force --month "$month"
    if [ $? -ne 0 ]; then
        echo "❌ Match failed for $month"
        continue
    fi
    
    # Phase 3: Enrich
    echo "  ✨ Enriching data..."
    python -m sotd.enrich.run --force --month "$month"
    if [ $? -ne 0 ]; then
        echo "❌ Enrich failed for $month"
        continue
    fi
    
    echo "✅ Successfully processed $month through all phases"
    echo "----------------------------------------"
done

echo "Pipeline processing complete!"
echo "====================================================="

# Show final status
echo "Final extracted count:"
find data/extracted -name "*.json" | wc -l

echo "Final matched count:"
find data/matched -name "*.json" | wc -l

echo "Final enriched count:"
find data/enriched -name "*.json" | wc -l 