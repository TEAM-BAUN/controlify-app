# -*- mode: python ; coding: utf-8 -*-
# Binary build: uv run pyinstaller controlify.spec
# Windows/Linux tek dosya, macOS .app bundle (onedir; onefile+bundle v7'de hata)
import sys

a = Analysis(
    ["app.py"],
    datas=[("assets", "assets")],
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        name="Controlify",
        console=False,
        upx=False,
        exclude_binaries=True,
    )
    coll = COLLECT(exe, a.binaries, a.datas, name="Controlify", upx=False)
    app = BUNDLE(
        coll,
        name="Controlify.app",
        bundle_identifier="com.controlify.app",
        info_plist={"NSHighResolutionCapable": True},
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        name="Controlify",
        console=False,
        upx=False,
    )
