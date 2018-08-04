# -*- mode: python -*-

block_cipher = None

def get_opencv_path():
    import cv2
    opencv_path = cv2.__path__[0]
    return opencv_path

a = Analysis(['analyse_video.py'],
             pathex=['.'],
             binaries=[],
             datas=[
                (get_opencv_path() + '/opencv_ffmpeg340.dll', '.'),
                ('./usr/pattern0.png', './usr'),
                ('./usr/pattern1.png', './usr')
             ],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
             
dict_tree = Tree(get_opencv_path(), prefix='cv2', excludes=["*.pyc"])
a.datas += dict_tree
a.binaries = filter(lambda x: 'cv2' not in x[0], a.binaries)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='analyse_video',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
