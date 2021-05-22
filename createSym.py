"""Create a new SymLink in a parent directory."""


from tkinter import Tk, filedialog as fdlg
from tkinter.ttk import Label, Button
from pathlib import Path


class main:
    """\
    Parameters
    ---------
    `parentdir` : str
        The path of the directory where the SymLink will be placed
    """

    def __init__(self, parentdir: str):
        self.initDir = Path(parentdir)
        self.root = Tk()
        wd = 400
        ht = 100
        self.root.title("Create Symbolic Link")
        self.root.attributes('-topmost', 1)
        x = ((self.root.winfo_screenwidth() - wd) // 2)
        y = ((self.root.winfo_screenheight() - ht) // 2)
        self.root.geometry(f'{wd}x{ht}+{x}+{y}')
        self.root.bind_all('<Escape>', lambda _: self.root.destroy())

        lbl1 = Label(master=self.root,
                     font='Ebrima 12',
                     text="Would you like to make a Symlink for a folder or a file?")
        lbl1.place(anchor='center',
                   relx=0.5,
                   rely=0.3)

        folder_btn = Button(master=self.root,
                            text="Folder",
                            underline=0,
                            command=self.linkFol,
                            width=10)
        folder_btn.place(anchor='center',
                         relx=0.25,
                         rely=0.66)
        folder_btn.focus_set()
        self.root.bind_all('<Return>', lambda _: folder_btn.invoke())

        file_btn = Button(master=self.root,
                          text=" File ",
                          command=self.linkFile,
                          width=10)
        file_btn.place(anchor='center',
                       relx=0.5,
                       rely=0.66)

        cancel_btn = Button(master=self.root,
                            text="Cancel",
                            command=self.root.destroy,
                            width=10)
        cancel_btn.place(anchor='center',
                         relx=0.75,
                         rely=0.66)

        self.root.mainloop()

    def linkFol(self): self.createLink('folder')
    def linkFile(self): self.createLink('file')

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
        self.root.destroy()
