from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from subprocess import run
from commandline import *
from textwrap import fill
from pathlib import Path
import logging

from winnotify import (
    Messagebox as Mbox,
    PlaySound
)

from ..lib.variables import (
    CRF_VALUES,
    COMP_FTYPES
)

WIDTH = 70
CLOSE_AFTER = 900


class CompressVideo:
    """Compress video files with specified extensions (from config.ini) within this folder (and optionally its subfolders) to HEVC/H.265.

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

        # resize window
        run(['powershell', '-command', ('$ps = (Get-Host).ui.rawui; '
                                        '$sz = $ps.windowsize; '
                                        '$sz.width = 70; '
                                        '$sz.height = 25; '
                                        '$ps.windowsize = $sz; '
                                        '$bf = $ps.buffersize; '
                                        '$bf.width = 70; '
                                        '$ps.buffersize = $bf')])
        fpath = Path(filepath).resolve()
        if fpath.is_dir():
            self.topfol = fpath
            kwargs = dict(
                message=f"Compressing {'|'.join(COMP_FTYPES)} files within <{fpath.name or fpath}> to HEVC/H.265. Recurse through subfolders?",
                buttons=('yes', 'no', 'cancel'))
        else:
            self.topfol = fpath.parent
            kwargs = dict(
                message=f"Compress <{fpath.name}> to HEVC/H.265?")
        PlaySound('Beep')
        dorun = Mbox.askquestion(title="Compress Video",
                                 **kwargs)
        if dorun == 'cancel':
            return
        elif dorun == 'yes':
            if fpath.is_dir():
                self.files = [f for f in self.topfol.rglob('*.*')
                              if f.suffix in COMP_FTYPES
                              and f.stat().st_size > (1024**3*2)]
            else:
                self.files = [fpath]
        elif fpath.is_dir():
            self.files = [f for f in self.topfol.glob('*.*')
                          if f.suffix in COMP_FTYPES
                          and f.stat().st_size > (1024**3*2)]

        self.start(fpath)

    def start(self, fpath: Path):
        # init vars
        t_start = datetime.now()
        self.errct = 0
        self.curct = 1
        # run
        self.totct = len(self.files)
        print(self.getStr(f"COMPRESSING {self.totct} ITEMS TO HEVC/H.265",
                          f"({fpath})"))
        with ThreadPoolExecutor(max_workers=2) as ex:
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
        ht = int(sizeout.split()[1].split('=')[1])
        # get quality
        for qty, crf in CRF_VALUES:
            if qty >= ht:
                break
        return (f'ffmpeg -hide_banner -y -i "{pth_in}" -movflags faststart -map 0 '
                f'-c:v libx265 -crf {crf} -preset slow -c:a copy "{pth_out}"; {timecmd}')

    def run(self, pth_in: Path) -> None:
        pth_out = pth_in.with_stem(f"[HEVC-AAC] {pth_in.stem}")
        if pth_out.suffix == '.avi':
            pth_out = pth_out.with_suffix('.mp4')
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
            if pth_out.stat().st_size < 100:
                resstr = f" COULDN'T COMPRESS {namestr}"
                pth_out.unlink()
            elif pth_out.stat().st_size < pth_in.stat().st_size:
                resstr = f" COMPRESSED {namestr}"
            else:
                resstr = f" COMPRESSION INEFFECTIVE {namestr}"
                pth_out.unlink()
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
