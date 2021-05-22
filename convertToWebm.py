"""Convert all *.gif and *.mp4 files within this folder and its subfolders to *.webm.

3rd-party Requirements
----------
FFmpeg (https://www.ffmpeg.org/)"""

from concurrent.futures import ThreadPoolExecutor
from winnotify import playSound
from datetime import datetime
from subprocess import run
from commandline import *
from textwrap import fill
from pathlib import Path
from re import findall

CONVERT_FROM = ('.gif', '.mp4', '.avi', '.wmv', '.mov')
CONVERT_TO = '.webm'
WIDTH = 70
CLOSE_AFTER = 900


class main:
    """-----
    Parameters
    ----------
    filepath (str): The path to either a directory to be searched or a video file
    """

    topfol: Path
    errlog: Path
    errct: int
    curct: int
    totct: int

    def __init__(self, filepath: str):
        # resize window
        run(['powershell', '-command', ('$ps = (Get-Host).ui.rawui; '
                                        '$sz = $ps.windowsize; '
                                        '$sz.width = 70; '
                                        '$sz.height = 25; '
                                        '$ps.windowsize = $sz; '
                                        '$bf = $ps.buffersize; '
                                        '$bf.width = 70; '
                                        '$ps.buffersize = $bf')])
        # init vars
        t_start = datetime.now()
        self.errct = 0
        self.curct = 1
        fpath = Path(filepath).resolve()
        self.topfol = (fpath if fpath.is_dir() else fpath.parent)
        self.errlog = Path(__file__).with_name('errorlog.txt')
        self.errlog.unlink(missing_ok=True)
        # run
        if fpath.is_dir():
            files = [pth_in for pth_in in self.topfol.rglob('*.*')
                     if pth_in.suffix.lower() in CONVERT_FROM]
        else:
            files = [fpath]
        self.totct = len(files)
        print(self.getStr(f"CONVERTING {self.totct} ITEMS TO WEBM",
                          f"({fpath})"))
        with ThreadPoolExecutor(max_workers=4) as ex:
            ex.map(self.run, files)
        # stop
        t_end = datetime.now()
        h, m, s = str(t_end - t_start).split(':')
        t_elapsed = ' '.join((f"{h:0>2}h", f"{m:0>2}m", f"{float(s):05.02f}s"))
        print(self.getStr("PROCESSING COMPLETE",
                          f"PROCESSED {self.totct} ITEMS WITH {self.errct} ERRORS",
                          f"TIME ELAPSED: {t_elapsed}"))
        # cleanup
        playSound('Beep')
        if self.errct:
            ans = askyesno('Would you like to open the errorlog?',
                           timeout=CLOSE_AFTER)
            if ans != 0:
                if not isinstance(ans, int):
                    playSound()
                openfile(self.errlog)
        else:
            self.errlog.unlink(missing_ok=True)
            RunCmd(['powershell', 'pause']).close_after(timeout=CLOSE_AFTER)

    @staticmethod
    def getStr(*args: str) -> str:
        return '\n'.join([f'{f" {s} " if s else s:=^{WIDTH}}'
                          for s in ('', *args, '')])

    @ staticmethod
    def getCmd(pth_in: Path, pth_out: Path) -> str:
        # get create/modify times
        st = pth_in.stat()
        dt = datetime.fromtimestamp
        frmt = "%A, %B %d, %Y %I:%M:%S %p"
        mt = dt(st.st_mtime).strftime(frmt)
        ct = dt(st.st_ctime).strftime(frmt)
        timecmd = (f'$o = Get-Item -LiteralPath "{pth_out}";'
                   f'$o.LastWriteTime = "{mt}";'
                   f'$o.CreationTime = "{ct}"')
        # get size
        sizecmd = ['ffprobe', pth_in, '-v', 'error', '-select_streams', 'v:0',
                   '-show_entries', 'stream=width,height', '-of', 'default=nw=1']
        sizeout: str = RunCmd(sizecmd, capture_output=True).communicate()[0]
        wd, ht = [int(sz.split('=')[1]) for sz in sizeout.split()]
        # get crop
        cropcmd = ['ffmpeg', '-hide_banner', '-i', pth_in, '-vframes', '10',
                   '-vf', 'cropdetect', '-f', 'null', '-']
        stderr: str = RunCmd(cropcmd, capture_output=True,
                             cwd=pth_in.parent).communicate()[1]
        try:
            crop = findall(r'crop=.+', stderr)[-1]
            cw, ch, cx, cy = findall(r'\d+', crop)
            if '-' in crop or (cw - cx) < wd / 2 or (ch - cy) < ht / 2:
                crop = f'crop={wd}:{ht}:0:0'
        except:
            crop = f'crop={wd}:{ht}:0:0'
        # get quality
        qualities = ((240, 37), (360, 36), (480, 33), (720, 32),
                     (1080, 31), (1440, 24), (2160, 15))
        for qty, crf in qualities:
            if qty >= ht:
                break
        return (f'ffmpeg -hide_banner -y -i "{pth_in}" -movflags faststart '
                f'-vf {crop} -c:v vp9 -b:v 0 -crf {crf} "{pth_out}";'
                f'{timecmd}')

    def run(self, pth_in: Path) -> None:
        pth_out = pth_in.with_suffix(CONVERT_TO)
        cmd = self.getCmd(pth_in, pth_out)
        returncode = RunCmd(['powershell', '-command', cmd],
                            console='new',
                            visibility='min').wait()
        name = fill(text=str(pth_in.relative_to(self.topfol).with_suffix('')),
                    width=(WIDTH - 14),
                    break_long_words=True,
                    subsequent_indent='  ')
        divstr = f"{f' {self.curct} of {self.totct} ':-^{WIDTH}}"
        namestr = f"<{name}>"
        self.curct += 1
        if pth_out.exists() and not returncode:
            resstr = f" CONVERTED {namestr}"
            pth_in.unlink()
        else:
            resstr = f" ERROR IN {namestr}"
            errstr = fill(text=(f"returncode <{returncode}>" if returncode
                                else f"<{pth_out}> could not be found"),
                          width=(WIDTH - 3),
                          break_long_words=True,
                          initial_indent='  ',
                          subsequent_indent='   ')
            with self.errlog.open('a') as f:
                f.write(f'{resstr}\n'
                        f'{errstr}\n'
                        f"{'#' * (WIDTH + 10)}\n"
                        '\n\n')
            playSound()
            openfile(self.errlog, 'min')
            self.errct += 1
        print(f'{divstr}\n{resstr}')
