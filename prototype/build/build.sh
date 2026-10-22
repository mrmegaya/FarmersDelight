#!/usr/bin/env bash
# Builds both APKs without the Android SDK.
# Needs: python3 with cryptography and Pillow. Signing key: set KEY=/path/to/key.pem (never commit it).
set -euo pipefail
cd "$(dirname "$0")"
: "${KEY:?Set KEY to the PEM signing key (private key + certificate). Use the same key for every release so updates install over older versions.}"
OUT=../../releases
python3 crops.py ../data/Tamil_Nadu_Crops_Grouped_by_Type.txt ../data/crops.json
python3 mkhtml.py
PKG=com.farmersdelight.farmer LABEL="FD Farmer" CAMERA=1 VC=${FARMER_VC:-3} VN=${FARMER_VN:-1.3} \
  python3 apkgen.py ../app/farmer.html icons/icon_farmer.png "$OUT/FD-Farmer-v${FARMER_VN:-1.3}.apk" "$KEY"
PKG=com.farmersdelight.app LABEL=FarmersDelight VC=${CONSUMER_VC:-3} VN=${CONSUMER_VN:-1.2} \
  python3 apkgen.py ../app/consumer.html icons/icon_consumer.png "$OUT/FarmersDelight-Consumer-v${CONSUMER_VN:-1.2}.apk" "$KEY"
for f in "$OUT"/*.apk; do python3 apkcheck.py "$f" | tail -1; done
