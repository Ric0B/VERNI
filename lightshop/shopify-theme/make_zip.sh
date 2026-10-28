#!/bin/sh
# Zip the theme contents for upload (Shopify wants layout/, sections/… at the zip root).
cd "$(dirname "$0")" && rm -f schichtlicht-theme.zip && zip -qr schichtlicht-theme.zip assets blocks config layout locales sections snippets templates && echo "wrote $(pwd)/schichtlicht-theme.zip"
