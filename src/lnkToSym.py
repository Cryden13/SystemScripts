from win32com.client import Dispatch
from pathlib import Path

from winnotify import Messagebox as Mbox


class LnkToSym:
    """Convert a link file (*.lnk) to a SymLink.
    """

    def __init__(self, linkpath: str):
        """\
        Parameters
        ---------
        linkpath (str): The path to an existing link file (*.lnk)
        """
        ans = Mbox.askquestion(title="Convert to Symlink",
                               message=f"Convert <{linkpath}> to SymLink?")
        if ans == 'no':
            return

        oldlnk = Dispatch("WScript.Shell").CreateShortcut(linkpath)
        target = Path(oldlnk.Targetpath)
        oldlnk = Path(linkpath)
        sym = oldlnk.with_suffix('')
        sym.symlink_to(target=target,
                       target_is_directory=target.is_dir())
        oldlnk.unlink()
