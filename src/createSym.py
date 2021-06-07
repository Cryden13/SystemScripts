from pathlib import Path

from tkinter.ttk import (
    Label,
    Button
)
from tkinter import (
    filedialog as fdlg,
    Tk
)


class CreateSym(Tk):
    """Create a new SymLink in a parent directory.
    """

    initDir: Path

    def __init__(self, parentdir: str):
        """\
        Parameters
        ---------
        parentdir (str): The path of the directory where the SymLink will be placed
        """

        self.initDir = Path(parentdir)
        Tk.__init__(self)
        wd = 400
        ht = 100
        self.title("Create Symbolic Link")
        self.attributes('-topmost', 1)
        x = ((self.winfo_screenwidth() - wd) // 2)
        y = ((self.winfo_screenheight() - ht) // 2)
        self.geometry(f'{wd}x{ht}+{x}+{y}')
        self.bind_all('<Escape>', lambda _: self.destroy())

        lbl1 = Label(master=self,
                     font='Ebrima 12',
                     text="Would you like to make a Symlink for a folder or a file?")
        lbl1.place(anchor='center',
                   relx=0.5,
                   rely=0.3)

        folder_btn = Button(master=self,
                            text="Folder",
                            underline=0,
                            command=lambda: self.createLink('folder'),
                            width=10)
        folder_btn.place(anchor='center',
                         relx=0.25,
                         rely=0.66)
        folder_btn.focus_set()
        self.bind_all('<Return>', lambda _: folder_btn.invoke())

        file_btn = Button(master=self,
                          text=" File ",
                          command=lambda: self.createLink('file'),
                          width=10)
        file_btn.place(anchor='center',
                       relx=0.5,
                       rely=0.66)

        cancel_btn = Button(master=self,
                            text="Cancel",
                            command=self.destroy,
                            width=10)
        cancel_btn.place(anchor='center',
                         relx=0.75,
                         rely=0.66)

        self.mainloop()

    def createLink(self, ftype: str) -> None:
        if ftype == 'folder':
            ask = fdlg.askdirectory
            def make(t: Path): t.mkdir(parents=True)
        else:
            ask = fdlg.askopenfilename
            def make(t: Path): t.touch()
        kwargs = dict(initialdir=self.initDir,
                      title=f'Select the {ftype} to link to:')
        sel = ask(**kwargs)
        if not sel:
            return
        target = Path(sel)
        if not target.exists():
            make(target)
        link = self.initDir.joinpath(target.stem)
        link.symlink_to(target=target,
                        target_is_directory=(ftype == 'folder'))
        self.destroy()
