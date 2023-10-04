from winnotify import Messagebox as Mbox
from subprocess import run
from pathlib import Path


class TakeOwnership:
    """Take ownership of a file or folder (optional: recursively)."""

    def __init__(self, filepath: str):
        """\
        Parameters
        ----------
        filepath (str): The path to a file or folder
        """

        path = Path(filepath).resolve()
        if not path.exists():
            raise FileNotFoundError(f'"{path}" could not be found')

        doiter = Mbox.askquestion(title=f"Register {path.name}",
                                  message="Iterate through subitems?",
                                  buttons=('yes', 'no', 'cancel'))
        if doiter == 'cancel':
            return

        cmd = f'subinacl /noverbose /{{}} "{path}{{}}" /setowner=%username% /grant=%username%=F'
        run(cmd.format('file', ''),
            shell=True)

        if doiter == 'yes':
            run(cmd.format('subdirectories', '\\*.*'),
                shell=True)
