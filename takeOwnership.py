"""Take ownership of a file or folder."""

from tkinter.messagebox import askyesnocancel
from subprocess import run
from pathlib import Path
from tkinter import Tk


def main(filepath: str):
    """\
    Parameters
    ----------
    `filepath` : str
        The path to a file or folder
    """

    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f'"{path}" could not be found')
    tk = Tk()
    tk.withdraw()
    doiter = askyesnocancel(title=f"Register {path.name}",
                            message="Iterate through subitems?")
    tk.destroy()
    if doiter == None:
        return
    cmd = f'subinacl /noverbose /{{}} "{path}{{}}" /setowner=%username% /grant=%username%=F'
    run(cmd.format('file', ''), shell=True)
    if doiter:
        run(cmd.format('subdirectories', '\\*.*'), shell=True)
