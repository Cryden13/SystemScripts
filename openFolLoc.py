"""Resolve all SymLinks in a folder, opening the resulting path."""

from commandline import RunCmd
from pathlib import Path


def main(folpath: str, parent: str = None):
    """\
    Parameters
    ----------
    folpath (str): The path to the folder

    parent (str, optional): [default=None] The path to the parent folder, if applicable
    """

    fol = Path(folpath)
    folpar = Path(parent) if parent else fol
    cmd = f"((New-Object -ComObject 'Shell.Application').Windows() | Where-Object LocationURL -ieq '{folpar.as_uri()}').Navigate('{fol.resolve()}')"
    RunCmd(['powershell', cmd], console='none', priority='high')
