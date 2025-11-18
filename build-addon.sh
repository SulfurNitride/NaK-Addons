#!/bin/bash
# Build script for NaK addons
# Usage: ./build-addon.sh <addon-dir> <version>

set -e

if [ $# -ne 2 ]; then
    echo "Usage: $0 <addon-dir> <version>"
    echo "Example: $0 spore-addon-example 1.0.0"
    exit 1
fi

ADDON_DIR="$1"
VERSION="$2"

if [ ! -d "$ADDON_DIR" ]; then
    echo "Error: Directory '$ADDON_DIR' not found"
    exit 1
fi

ADDON_ID=$(python3 -c "import json; print(json.load(open('$ADDON_DIR/addon.json'))['id'])")
OUTPUT_FILE="${ADDON_ID}-${VERSION}.zip"

echo "Building: $OUTPUT_FILE"

TEMP_DIR=$(mktemp -d)
cp -r "$ADDON_DIR"/* "$TEMP_DIR/"
find "$TEMP_DIR" -name "*.pyc" -delete
find "$TEMP_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

cd "$TEMP_DIR"
zip -r "../$OUTPUT_FILE" ./*
cd - > /dev/null
mv "$TEMP_DIR/../$OUTPUT_FILE" "./$OUTPUT_FILE"
rm -rf "$TEMP_DIR"

echo "✓ Built: $OUTPUT_FILE"
