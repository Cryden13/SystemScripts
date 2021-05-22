from subprocess import Popen, CREATE_NEW_CONSOLE
from winnotify import playSound


def _show_info(win: bool, msgType: str, fname: str, msg: str):
    playSound('Beep')
    if win:
        info = f"{fname} {msgType}:"
        output = (f"\"{'='*25}`n"
                  f"{info}`n"
                  f"{'='*25}`n"
                  f"{msg}`n`n"
                  "Press 'return' to close\"")
        Popen(['powershell', 'Read-Host',
               output.replace('\n', '`n')],
              creationflags=CREATE_NEW_CONSOLE)
    else:
        print(msg)
