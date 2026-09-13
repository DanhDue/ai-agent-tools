#!/bin/bash
# Script to copy secure configuration files from secureFiles/ to Android and iOS project directories.

# Ensure we are in the project root
if [ ! -d "secureFiles" ]; then
    echo "Error: secureFiles directory not found. Please run this script from the project root."
    exit 1
fi

echo "Copying Secure Configurations..."

# 1. Android: google-services.json
# Destination: android/app/src/<flavor>/google-services.json

# Copy for dev
if [ -f "secureFiles/dev/google-services.json" ]; then
    mkdir -p android/app/src/dev
    cp secureFiles/dev/google-services.json android/app/src/dev/google-services.json
    echo "✅ Copied android/app/src/dev/google-services.json"
else
    echo "⚠️  Missing secureFiles/dev/google-services.json"
fi

# Copy for stg
if [ -f "secureFiles/stg/google-services.json" ]; then
    mkdir -p android/app/src/stg
    cp secureFiles/stg/google-services.json android/app/src/stg/google-services.json
    echo "✅ Copied android/app/src/stg/google-services.json"
else
    echo "⚠️  Missing secureFiles/stg/google-services.json"
fi

# Copy for prd
if [ -f "secureFiles/prd/google-services.json" ]; then
    mkdir -p android/app/src/prd
    cp secureFiles/prd/google-services.json android/app/src/prd/google-services.json
    echo "✅ Copied android/app/src/prd/google-services.json"
else
    echo "⚠️  Missing secureFiles/prd/google-services.json"
fi

# 2. iOS: GoogleService-Info.plist
# Destination: ios/Runner/Firebase/GoogleService-Info.<flavor>.plist

mkdir -p ios/Runner/Firebase

# Copy for dev
if [ -f "secureFiles/dev/GoogleService-Info.plist" ]; then
    cp secureFiles/dev/GoogleService-Info.plist ios/Runner/Firebase/GoogleService-Info.dev.plist
    echo "✅ Copied ios/Runner/Firebase/GoogleService-Info.dev.plist"
else
    echo "⚠️  Missing secureFiles/dev/GoogleService-Info.plist"
fi

# Copy for stg
if [ -f "secureFiles/stg/GoogleService-Info.plist" ]; then
    cp secureFiles/stg/GoogleService-Info.plist ios/Runner/Firebase/GoogleService-Info.stg.plist
    echo "✅ Copied ios/Runner/Firebase/GoogleService-Info.stg.plist"
else
    echo "⚠️  Missing secureFiles/stg/GoogleService-Info.plist"
fi

# Copy for prd
if [ -f "secureFiles/prd/GoogleService-Info.plist" ]; then
    cp secureFiles/prd/GoogleService-Info.plist ios/Runner/Firebase/GoogleService-Info.prd.plist
    echo "✅ Copied ios/Runner/Firebase/GoogleService-Info.prd.plist"
else
    echo "⚠️  Missing secureFiles/prd/GoogleService-Info.plist"
fi

echo "Secure configurations copied successfully."
