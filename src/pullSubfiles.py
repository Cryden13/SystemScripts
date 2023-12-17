from pathlib import Path
from time import sleep

from winnotify import (
    Messagebox as Mbox,
    PlaySound
)
from re import (
    search,
    sub
)


class PullSubfiles:
    """Move all files in this folder's subdirectories to this folder, recursively."""

    def __init__(self, topdir: str):
        """\
        Parameters
        ----------
        topdir (str): the top-most directory to recurse from
        """

        maindir = Path(topdir).resolve()
        while not maindir.is_dir():
            maindir = maindir.parent
        filect = len(tuple(f for f in maindir.rglob('*') if not f.is_dir()))
        PlaySound("Beep")
        ans = Mbox.askquestion(title="Pull Subfiles",
                               message=f"Pull {filect} subfiles to <{maindir}>?")
        if ans == 'no':
            return
        subdirs = [d for d in maindir.iterdir() if d.is_dir()]
        for d in subdirs:
            for file in [f for f in d.rglob('*') if not f.is_dir()]:
                new = maindir.joinpath(file.name)
                while new.exists():
                    m = search(r' \((\d+)\)$', new.stem)
                    ct = (int(m.group(1)) + 1) if m else 1
                    nm = sub(r' \(\d+\)$|$', f' ({ct})', new.stem, 1)
                    new = new.with_stem(nm)
                file.rename(new)
            for fol in sorted([f for f in d.rglob('*') if f.is_dir()], reverse=True):
                fol.rmdir()
            d.rmdir()
        sleep(0.5)
        if [d for d in maindir.iterdir() if d.is_dir()]:
            PullSubfiles(maindir)
        PlaySound('Beep')
