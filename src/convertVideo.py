from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from subprocess import run
from commandline import *
from textwrap import fill
from pathlib import Path
from re import findall
import logging

from winnotify import (
    Messagebox as Mbox,
    PlaySound
)

from ..lib.variables import (
    CRF_VALUES,
    CONV_FTYPES,
    CONV_TO,
    CONV_CODEC
)

WIDTH = 70
CLOSE_AFTER = 900
CONV_STR = CONV_TO[1:].title()


class ConvertVideo:
    """Convert video files with specified extensions (from config.ini) within this folder (and optionally its subfolders) to the preferred format.

    3rd-party Requirements
    ----------
    FFmpeg (https://www.ffmpeg.org/)
    """

    topfol: Path
    files: list[Path]
    errct: int
    curct: int
    totct: int

    def __init__(self, filepath: str):
        """\
        Parameters
        ----------
        filepath (str): The path to either a directory to be searched or a video file
        """

        fpath = Path(filepath).resolve()
        if fpath.is_dir():
            self.topfol = fpath
            kwargs = dict(
                message=f"Converting video files within '{fpath.name}' to {CONV_STR}. Recurse through subfolders?",
                buttons=('yes', 'no', 'cancel'))
        else:
            self.topfol = fpath.parent
            kwargs = dict(
                message=f"Convert '{fpath.name}' to {CONV_STR}?")
        PlaySound('Beep')
        dorun = Mbox.askquestion(title=f"Convert To {CONV_STR}",
                                 **kwargs)
        if dorun == 'cancel':
            return
        elif dorun == 'yes':
            self.files = [pth_in for pth_in in self.topfol.rglob('*.*')
                          if pth_in.suffix.lower() in CONV_FTYPES]
        elif fpath.is_dir():
            self.files = [pth_in for pth_in in self.topfol.glob('*.*')
                          if pth_in.suffix.lower() in CONV_FTYPES]
        else:
            self.files = [fpath]
        self.start(fpath)

    def start(self, fpath: Path):
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
        # run
        self.totct = len(self.files)
        print(self.getStr(f"CONVERTING {self.totct} ITEMS TO {CONV_STR}",
                          f"({fpath})"))
        with ThreadPoolExecutor(max_workers=4) as ex:
            ex.map(self.run, self.files)
        # stop
        t_end = datetime.now()
        h, m, s = str(t_end - t_start).split(':')
        t_elapsed = ' '.join((f"{h:0>2}h", f"{m:0>2}m", f"{float(s):05.02f}s"))
        print(self.getStr("PROCESSING COMPLETE",
                          f"PROCESSED {self.totct} ITEMS WITH {self.errct} ERRORS",
                          f"TIME ELAPSED: {t_elapsed}"))
        # cleanup
        PlaySound('Beep')
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
        for qty, crf in CRF_VALUES:
            if qty >= ht:
                break
        return (f'ffmpeg -hide_banner -y -i "{pth_in}" -movflags faststart '
                f'-vf {crop} -c:v {CONV_CODEC} -b:v 0 -crf {crf} "{pth_out}"; '
                f'{timecmd}')

    def run(self, pth_in: Path) -> None:
        pth_out = pth_in.with_suffix(CONV_TO)
        cmd = self.getCmd(pth_in, pth_out)
        returncode = RunCmd(['powershell', '-command', cmd],
                            console='new',
                            visibility='min').wait()
        name = fill(text=pth_in.relative_to(self.topfol).stem,
                    width=(WIDTH - 14),
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
                          initial_indent='  ',
                          subsequent_indent='   ')
            logging.exception(f'{resstr}\n'
                              f'{errstr}\n'
                              f"{'#' * (WIDTH + 10)}\n"
                              '\n\n')
            self.errct += 1
        print(f'{divstr}\n{resstr}')
