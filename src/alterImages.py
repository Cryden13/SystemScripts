from joinwith import joinwith
from subprocess import run
from pathlib import Path

from winnotify import (
    InputDialog as InDlg,
    Messagebox as Mbox,
    PlaySound
)

from ..lib.variables import ALTER_FTYPES


class AlterImages:
    """Resize image files with specified extensions (from config.ini) within this folder to 2k and optionally convert them to jpg.

    3rd-party Requirements
    ----------
    ImageMagick (https://imagemagick.org/)
    """

    def __init__(self, workingdir: str):
        """\
        Parameters
        ----------
        workingdir (str): The path of the directory that contains the images
        """

        # init vars
        dirname = Path(workingdir).resolve()
        res = {'None': '',
               '1280x720': 'HD',
               '1920x1080': 'FHD',
               '2560x1440': '2K'}
        # get preferences
        ans = InDlg.multiinput(title="Alter Images",
                               message=f"Altering image files in <{dirname}>.",
                               input_fields=[
                                   ('Conversion', InDlg._combobox(options=['None', '.jpg', '.png'],
                                                                  default='None')),
                                   ('Resize', InDlg._combobox(options=res.keys(),
                                                              default='2560x1440')),
                                   ('Recurse folders', InDlg._checkbox())
                               ])
        if not ans:
            return
        # get vars
        convert = ans['Conversion'] if ans['Conversion'] != 'None' else ''
        resize = f"-resize {ans['Resize']}" if ans['Resize'] != 'None' else ''
        if not convert and not resize:
            Mbox.showerror(title="AlterImages Error",
                           message="There's nothing to do!")
            return
        resstr = f"({res.get(ans['Resize'])}) " if resize else ''
        recurse = ans['Recurse folders']
        # find files
        func = dirname.rglob if recurse else dirname.glob
        files = [f'"{f.resolve()}"' for f in func('*.*')
                 if f.suffix in ALTER_FTYPES]
        # build command
        fname, ext = ('t', convert) if convert else ('f', '')
        cmd = (f'magick {files} {resize} '
               f'-set filename:f "%{fname}" '
               f'+adjoin "{resstr}%[filename:f]{ext}"')
        run(cmd, cwd=dirname)
        PlaySound('Beep')
