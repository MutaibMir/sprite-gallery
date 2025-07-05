[app]
title = SpriteApp
package.name = spriteapp
package.domain = org.kivy
source.dir = .
source.include_exts = py,png,jpg,kv,json
version = 1.0
orientation = portrait
fullscreen = 0
log_level = 2
main.py = main.py
requirements = python3,kivy,pillow,cython==0.29.33
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png
android.permissions = MANAGE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.extra_manifest_entries = <application android:requestLegacyExternalStorage="true"/>
android.api = 33
android.minapi = 21
android.ndk = 25b
android.build_tools_version = 36.0.0
android.archs = arm64-v8a
android.allow_backup = True
android.hide_statusbar = False
android.strip = False

[buildozer]
log_level = 2
warn_on_root = 0
android.accept_sdk_license = True
android.skip_update = False
android.sdk_path = $HOME/android-sdk
android.ndk_path = $HOME/.buildozer/android/platform/android-ndk-r23b
