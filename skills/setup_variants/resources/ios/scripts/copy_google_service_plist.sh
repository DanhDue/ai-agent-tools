#!/bin/sh

# Default to dev if not found
ENVIRONMENT="dev"

if [[ "$CONFIGURATION" == *"dev"* ]]; then
    ENVIRONMENT="dev"
elif [[ "$CONFIGURATION" == *"stg"* ]]; then
    ENVIRONMENT="stg"
elif [[ "$CONFIGURATION" == *"prd"* ]]; then
    ENVIRONMENT="prd"
fi

# Path to the GoogleService-Info.plist in the project (copied by copy_secure_configurations skill)
# Located at ios/Runner/Firebase/GoogleService-Info.<flavor>.plist
GOOGLE_SERVICE_INFO_PLIST_FROM="${PROJECT_DIR}/Runner/Firebase/GoogleService-Info.${ENVIRONMENT}.plist"

# Destination path inside the app bundle
BUILD_APP_DIR="${BUILT_PRODUCTS_DIR}/${PRODUCT_NAME}.app"
GOOGLE_SERVICE_INFO_PLIST_TO="${BUILD_APP_DIR}/GoogleService-Info.plist"

echo "Copying GoogleService-Info.plist from ${GOOGLE_SERVICE_INFO_PLIST_FROM} to ${GOOGLE_SERVICE_INFO_PLIST_TO}"

if [ -f "${GOOGLE_SERVICE_INFO_PLIST_FROM}" ]; then
    cp "${GOOGLE_SERVICE_INFO_PLIST_FROM}" "${GOOGLE_SERVICE_INFO_PLIST_TO}"
    echo "Successfully copied GoogleService-Info.plist"
else
    echo "warning: GoogleService-Info.plist not found at ${GOOGLE_SERVICE_INFO_PLIST_FROM}"
    # Fail build for release/stg/prd if missing? Maybe valid for initial setup to just warn.
    # exit 1 
fi
