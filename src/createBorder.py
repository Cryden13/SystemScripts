from win32gui import (
    GetForegroundWindow as GetForeWin,
    SetWindowLong,
    GetWindowRect
)
from tkinter import (
    Tk,
    Frame
)


class CreateBorder:
    """Create a topmost window that acts as a border around the currently active window.
    """

    def __init__(self, *rect):
        """\
        Parameters
        ----------
        rect (list[int, int, int, int], optional): [default=None] if provided, must be [left, top, right, bottom] of current window
        """

        topWin = GetForeWin()
        x, y, w, h = rect if len(rect) == 4 else GetWindowRect(topWin)
        root = Tk()
        root.overrideredirect(True)
        root.title("-*Filter*-")
        root.config(bg='red')
        root.attributes('-transparentcolor', 'black',
                        '-topmost', True,
                        '-alpha', 0.5)
        root.geometry('{}x{}+{}+{}'.format(w, h, x, y))
        f = Frame(root, bg='black')
        f.place(anchor='center',
                relx=0.5,
                rely=0.5,
                width=-6,
                relwidth=1,
                height=-6,
                relheight=1)
        root.update_idletasks()
        SetWindowLong(GetForeWin(), -8, topWin)

        root.mainloop()
