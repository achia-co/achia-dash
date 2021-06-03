# -*- mode: python ; coding: utf-8 -*-
import importlib
import pathlib
from PyInstaller.utils.hooks import collect_submodules, copy_metadata
ROOT = pathlib.Path(importlib.import_module("chia").__file__).absolute().parent.parent
from pkg_resources import get_distribution
block_cipher = None


chia_mod = importlib.import_module("chia")
dll_paths = ROOT / "*.dll"

binaries = [
    (
        dll_paths,
        ".",
    ),
    (
        "C:\\Windows\\System32\\msvcp140.dll",
        ".",
    ),
    (
        "C:\\Windows\\System32\\vcruntime140_1.dll",
        ".",
    ),
]
	
version_data = copy_metadata(get_distribution("chia-blockchain"))[0]

datas = []

datas.append((f"{ROOT}/chia/util/english.txt", "chia/util"))
datas.append((f"{ROOT}/chia/util/initial-config.yaml", "chia/util"))
datas.append((f"{ROOT}/chia/wallet/puzzles/*.hex", "chia/wallet/puzzles"))
datas.append((f"{ROOT}/chia/ssl/*", "chia/ssl"))
datas.append((f"{ROOT}/mozilla-ca/*", "mozilla-ca"))
datas.append(version_data)

a = Analysis(['run.py'],
             pathex=["run.py"],
             binaries=binaries,
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='run',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='img\\logo.ico')
