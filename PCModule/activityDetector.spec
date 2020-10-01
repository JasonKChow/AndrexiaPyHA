# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['activityDetector.py'],
             pathex=['D:\\Documents\\AndrexiaPyHA\\PCModule'],
             binaries=[],
             datas=[('.\\icons\\activityDetectorOn.ico', 'icons'), ('.\\icons\\activityDetectorOff.ico', 'icons'),
                ('./config.json', '.')],
             hiddenimports=['pkg_resources', 'infi.systray'],
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
          [],
          exclude_binaries=True,
          name='activityDetector',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='activityDetector')
