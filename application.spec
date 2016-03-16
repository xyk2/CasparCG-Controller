# -*- mode: python -*-
a = Analysis(['application.py'],
             pathex=['C:\Users\XYK\Desktop\Dropbox\Choxue-casparcg'],
             #pathex=['/Users/XYK/Desktop/Dropbox/Choxue-casparcg'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)

##### include mydir in distribution #######
def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
            rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    for f in files:
        extra_datas.append((f, f, 'DATA'))

    return extra_datas
###########################################

a.datas += [('_001 Commentators-CG_00061.png','_001 Commentators-CG_00061.png','DATA')]
a.datas += [('_002 Officials-CG_00083.png','_002 Officials-CG_00083.png','DATA')]
a.datas += [('_003 Score line-CG_00060.png','_003 Score line-CG_00060.png','DATA')]
a.datas += [('_004 Score 2-CG_00050.png','_004 Score 2-CG_00050.png','DATA')]
a.datas += [('_009 Standings-CG_00114.png','_009 Standings-CG_00114.png','DATA')]
a.datas += [('_010 Score by quarter-CG_00065b.png','_010 Score by quarter-CG_00065b.png','DATA')]
a.datas += [('_011 Player stats box-CG_00074.png','_011 Player stats box-CG_00074.png','DATA')]
a.datas += [('_012 Game stats-CG_00107.png','_012 Game stats-CG_00107.png','DATA')]
a.datas += [('_015 Starting lineup faces-CG_00146.png','_015 Starting lineup faces-CG_00146.png','DATA')]
a.datas += [('_017 Score 3-CG_00066.png', '_017 Score 3-CG_00066.png','DATA')]
a.datas += [('settings.ini', 'settings.ini','DATA')]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='application',
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='application')