#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
android_jar=${ANDROID_JAR:-/usr/lib/android-sdk/platforms/android-23/android.jar}
signing_env=${SIGNING_ENV:-/etc/rep-trainer/android-signing.env}
output=${APK_OUTPUT:-$root/android/build/rep-trainer.apk}
build=$root/android/build

if [ ! -f "$android_jar" ]; then echo "Android SDK platform 23 is required" >&2; exit 1; fi
if [ ! -f "$signing_env" ]; then echo "Signing environment file is required" >&2; exit 1; fi
set -a
. "$signing_env"
set +a
: "${ANDROID_STORE_PASS:?Missing signing password}"
: "${ANDROID_KEYSTORE:?Missing Android keystore path}"

mkdir -p "$build/classes" "$(dirname "$output")"
aapt package -f -M "$root/android/AndroidManifest.xml" -S "$root/android/res" \
    -I "$android_jar" -F "$build/resources.apk"
javac --release 7 -cp "$android_jar" -d "$build/classes" \
    "$root/android/src/online/chenxiouyang/reptrainer/MainActivity.java"
dalvik-exchange --dex --output="$build/classes.dex" "$build/classes"
cp "$build/resources.apk" "$build/unsigned.apk"
python3 - "$build/unsigned.apk" "$build/classes.dex" <<'PY'
import sys
import zipfile

with zipfile.ZipFile(sys.argv[1], "a", compression=zipfile.ZIP_DEFLATED) as package:
    package.write(sys.argv[2], "classes.dex")
PY
zipalign -f 4 "$build/unsigned.apk" "$build/aligned.apk"
apksigner sign --ks "$ANDROID_KEYSTORE" --ks-key-alias reptrainer \
    --ks-pass env:ANDROID_STORE_PASS --key-pass env:ANDROID_STORE_PASS \
    --out "$output" "$build/aligned.apk"
apksigner verify --verbose "$output"
echo "APK ready: $output"
