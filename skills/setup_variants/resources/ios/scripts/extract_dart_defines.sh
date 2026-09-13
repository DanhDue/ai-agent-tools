#!/bin/sh

# Output file
OUTPUT_FILE="${SRCROOT}/Flutter/${1:-Define}.xcconfig"

# Function to decode base64
function entry_decode() { echo "${*}" | base64 --decode; }

# Check if DART_DEFINES is set
if [ -z "$DART_DEFINES" ]; then
    echo "// No DART_DEFINES found, skipping..." > "$OUTPUT_FILE"
    exit 0
fi

# Decode and write to file
echo "// Generated file, do not edit" > "$OUTPUT_FILE"

IFS=',' read -r -a define_items <<< "$DART_DEFINES"

for item in "${define_items[@]}"; do
    decoded=$(entry_decode "$item")
    # Verify it maps to KEY=VALUE pattern
    if [[ $decoded == *"="* ]]; then
         # Prepend DART_DEFINES_ match Android logic
         echo "DART_DEFINES_$decoded" >> "$OUTPUT_FILE"
    fi
done
