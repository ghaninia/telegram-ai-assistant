#!/usr/bin/env bash
# Build dist/TelegramAIBot.app and dist/TelegramAIBot.dmg.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"
APP_NAME="TelegramAIBot"
WORK="$ROOT/build"

source .venv/bin/activate
pip install -q -e ".[dev]"

pyinstaller --noconfirm --clean --windowed \
  --name "$APP_NAME" \
  --icon "$ROOT/packaging/AppIcon.icns" \
  --osx-bundle-identifier com.amin.telegramaibot \
  --paths "$ROOT/src" \
  --add-data "$ROOT/src/telegram_ai_bot/resources:telegram_ai_bot/resources" \
  --exclude-module tkinter \
  --distpath "$ROOT/dist" --workpath "$WORK" --specpath "$WORK" \
  "$ROOT/packaging/launcher.py"

# Drag-and-drop installer with an Applications shortcut.
rm -rf "$WORK/dmg" "dist/$APP_NAME.dmg"
mkdir -p "$WORK/dmg"
cp -R "dist/$APP_NAME.app" "$WORK/dmg/"
ln -s /Applications "$WORK/dmg/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$WORK/dmg" -ov -format UDZO "dist/$APP_NAME.dmg" >/dev/null

# Remove intermediates; keep only the .app and .dmg.
rm -rf "$WORK" "dist/$APP_NAME"
echo "Built dist/$APP_NAME.app and dist/$APP_NAME.dmg"
