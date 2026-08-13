import platform

ffmpeg_exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[
        (f"ffmpeg/{ffmpeg_exe}", "ffmpeg"),
    ],
    datas=[
        ("LICENSE_FFMPEG.txt", "."),
        ("LICENSE", "."),
    ],
    hiddenimports=["chardet"],
)

pyz = PYZ(a.pure)

exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="SubBake", debug=False, strip=False, upx=True, upx_exclude=["ffmpeg", "ffmpeg.exe"], console=False, icon=None)