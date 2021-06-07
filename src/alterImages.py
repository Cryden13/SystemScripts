from joinwith import joinwith
from subprocess import run
from pathlib import Path

from winnotify import (
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

        dirname = Path(workingdir).resolve()
        convert = Mbox.askquestion(title="Resize and Convert",
                                   message=f"Resizing files in <{dirname}> to 2k. Also convert to jpg?",
                                   buttons=('yes', 'no', 'cancel'))
        if convert == 'cancel':
            return
        recurse = Mbox.askquestion(title="Recurse?",
                                   message="Recurse through subfolders?")
        func = dirname.rglob if recurse == 'yes' else dirname.glob
        files = [f.resolve() for f in func('*.*')
                 if f.suffix in ALTER_FTYPES]
        files = joinwith(files, ' ', ' ', '"{}"')
        fname, cnv = ('t', '.jpg') if convert == 'yes' else ('f', '')
        cmd = (f'magick {files} -resize 2560x1440 '
               f'-set filename:f "%{fname}" '
               f'+adjoin "(2k) %[filename:f]{".jpg" if cnv else ""}"')
        run(cmd, cwd=dirname)
        PlaySound('Beep')
