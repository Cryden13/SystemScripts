"""Resize all image files in a directory to 2k and optionally convert them to jpg.

3rd-party Requirements
----------
ImageMagick (https://imagemagick.org/)"""

from tkinter import Tk, messagebox as mbox
from joinwith import joinwith
from subprocess import run
from pathlib import Path

file_types = ('.bmp', '.jpeg', '.jpg', '.png', '.tiff', '.webp')


def main(workingdir: str):
    """\
    Parameters
    ----------
    `workingdir` : str
        The path of the directory that contains the images
    """

    dirname = Path(workingdir)
    files = [f.resolve() for f in dirname.iterdir()
             if f.suffix in file_types]
    files = joinwith(files, ' ', ' ', '"{}"')

    tk = Tk()
    tk.withdraw()
    doFrmt = mbox.askyesnocancel(title="Reformat",
                                 message="Reformat files to jpg?")
    tk.destroy()
    if doFrmt == None:
        return
    cmd = (f'magick {files} -resize 2560x1440 '
           f'-set filename:f "%{"t" if doFrmt else "f"}" '
           '+adjoin "(2k) %[filename:f]'
           f'{".jpg" if doFrmt else ""}"')
    run(cmd, cwd=dirname)
