[app]
title = Sprite Viewer
package.name = spriteviewer
package.domain = org.kivy
source.dir = .
source.include_exts = py,png,jpg,kv,json
version = 1.0

requirements = python3,kivy,pillow

orientation = portrait
fullscreen = 1

# Launcher icon (must be placed in project root as icon.png)
icon.filename = icon.png

# Permissions to access /sdcard
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Android version settings (safe for Android 10–11)
android.api = 30
android.minapi = 21
android.target = 30

# Keep screen on while running
android.keep_active = 1

[buildozer]
log_level = 2
warn_on_root = 0
