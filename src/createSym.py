from pathlib import Path

from PyQt5.QtWidgets import (
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QLabel
)

from winnotify import PlaySound


class CreateSym(QDialog):
    """Create a new SymLink in a parent directory."""

    parent_dir: Path

    def __init__(self, parentdir: str):
        """\
        Parameters
        ---------
        parentdir (str): The path of the directory where the SymLink will be placed
        """

        self.parent_dir = Path(parentdir)
        QDialog.__init__(self)
        self.setMinimumWidth(400)
        self.setMinimumHeight(100)
        self.setWindowTitle("Create Symbolic Link")

        vlayout = QVBoxLayout(self)
        lbl = QLabel(parent=self,
                     text="Would you like to make a Symlink for a directory or a file?")
        vlayout.addWidget(lbl)

        btnlayout = QHBoxLayout()
        btnlayout.setSpacing(20)
        btnlayout.setContentsMargins(50, 0, 50, 0)

        folder_btn = QPushButton(text="Directory")
        folder_btn.clicked.connect(lambda *_: self.createLink('dir'))
        btnlayout.addWidget(folder_btn)

        file_btn = QPushButton(text="File")
        file_btn.clicked.connect(lambda *_: self.createLink('file'))
        btnlayout.addWidget(file_btn)

        cancel_btn = QPushButton(text="Cancel")
        cancel_btn.clicked.connect(self.close)
        btnlayout.addWidget(cancel_btn)

        vlayout.addLayout(btnlayout)

        self.exec()

    def createLink(self, ftype: str) -> None:
        kwargs = dict(parent=self,
                      caption=f'Select the {ftype} to link to:',
                      directory=str(self.parent_dir))
        if ftype == 'dir':
            sel = QFileDialog.getExistingDirectory(**kwargs)
        else:
            sel = QFileDialog.getOpenFileName(**kwargs)[0]
        if not sel:
            return
        print(sel)
        target = Path(sel)
        link = self.parent_dir.joinpath(target.stem)
        n = 1
        while link.exists():
            link = link.with_stem(f"{link.stem}({n})")
            n += 1
        link.symlink_to(target=target,
                        target_is_directory=(ftype == 'dir'))
        PlaySound("Beep")
        self.close()
