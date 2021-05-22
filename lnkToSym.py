"""Convert a link file (*.lnk) to a SymLink."""


from win32com.client import Dispatch
from pathlib import Path


def main(linkpath: str):
    """\
    Parameters
    ---------
    `linkpath` : str
        The path to an existing link file (*.lnk)
    """

    oldlnk = Dispatch("WScript.Shell").CreateShortcut(linkpath)
    target = Path(oldlnk.Targetpath)
    oldlnk = Path(linkpath)
    sym = oldlnk.with_suffix('')
    sym.symlink_to(target=target,
                   target_is_directory=target.is_dir())
    oldlnk.unlink()
