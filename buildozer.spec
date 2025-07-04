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

# Custom app icon
icon.filename = icon.png

# Permissions to access external storage
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Target a stable, working version of Android build tools
android.build_tools_version = 34.0.0
android.api = 30
android.minapi = 21
android.target = 30

# Keep screen on
android.keep_active = 1

[buildozer]
log_level = 2
warn_on_root = 0
