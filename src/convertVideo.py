from concurrent.futures import ThreadPoolExecutor
from typing import Optional as O
from textwrap import TextWrapper
from datetime import datetime
from ..lib.variables import *
from subprocess import run
from commandline import *
from pathlib import Path
import logging

from winnotify import (
    InputDialog as InDlg,
    Messagebox as Mbox,
    PlaySound
)
from re import (
    findall as re_findall,
    search as re_search
)


class _Opt:
    thread_ct: int = CONV_THREADS
    output: str = ''
    vid_strm: str = 'all'
    aud_strm: str = 'all'
    sub_strm: str = 'all'
    overwrite: bool = False
    isdir: bool = False
    keepfail: bool = False
    recurse: bool = False
    playtime: str = CONV_CUTOFF

    @classmethod
    def getInput(cls, fpath: Path) -> bool:
        fields = [
            ('Video stream', InDlg._combobox(options=['all', *[str(i) for i in range(CONV_STREAMS)]],
                                             default=cls.vid_strm)),
            ('Audio stream', InDlg._combobox(options=['all', *[str(i) for i in range(CONV_STREAMS)]],
                                             default=cls.aud_strm)),
            ('Subtitle stream', InDlg._combobox(options=['all', *[str(i) for i in range(CONV_STREAMS)]],
                                                default=cls.sub_strm)),
            ('Overwrite original', InDlg._checkbox(default=cls.overwrite))
        ]
        if fpath.is_dir():
            cls.isdir = True
            fields.insert(0, ('Output format', InDlg._combobox(options=['both', '.mkv', '.webm'],
                                                               default='both')))
            fields += [
                ('Keep failures', InDlg._checkbox(default=cls.keepfail)),
                ('Recurse folders', InDlg._checkbox(default=cls.recurse)),
                ('Webm cutoff (sec)', InDlg._spinbox(min=0,
                                                     max=3600,
                                                     default=cls.playtime)),
                ('Thread count', InDlg._spinbox(min=1,
                                                max=(3 if CONV_NVENC else 20),
                                                default=cls.thread_ct))
            ]
            msg = (f"Compress/Convert {', '.join(CONV_FTYPES)} "
                   f"files within <{fpath.name}>.")
        else:
            dur: str = run(['ffprobe', '-v', 'error', '-show_entries',
                            'format=duration', '-of', 'csv=p=0', '-i', fpath],
                           capture_output=True,
                           text=True).stdout
            fields.insert(0, ('Output format', InDlg._combobox(options=['.mkv', '.webm'],
                                                               default=('.mkv' if float(dur) >= cls.playtime else '.webm'))))
            msg = f"Compress/Convert <{fpath.name}>."
        PlaySound('Beep')
        ans = InDlg.multiinput(
            title="Convert Video - Options",
            message=f"{msg}\n",
            input_fields=fields
        )
        if ans:
            cls.output = ans['Output format']
            cls.vid_strm = ans['Video stream']
            cls.aud_strm = ans['Audio stream']
            cls.sub_strm = ans['Subtitle stream']
            cls.overwrite = ans['Overwrite original']
            if cls.isdir:
                cls.keepfail = ans['Keep failures']
                cls.recurse = ans['Recurse folders']
                cls.playtime = ans['Webm cutoff (sec)']
                cls.thread_ct = ans['Thread count']
            return True
        else:
            return False

    @classmethod
    def getInfo(cls) -> list[str]:
        out = [
            f"Output format: {cls.output.lstrip('.').upper()}",
            f"Video stream: {cls.vid_strm}",
            f"Audio stream: {cls.aud_strm}",
            f"Subtitle stream: {cls.sub_strm}",
            f"Overwrite original: {'yes' if cls.overwrite else 'no'}"
        ]
        if cls.isdir:
            out.insert(0, f"Running threads: {cls.thread_ct}")
            out += [f"Keep failures: {'yes' if cls.keepfail else 'no'}",
                    f"Recurse folders: {'yes' if cls.recurse else 'no'}"]
            if cls.output == 'both':
                out.append(f"Playtime cutoff: {cls.playtime}s")
        sz1 = max(*[len(s) for i, s in enumerate(out) if not i % 2])
        sz2 = max(*[len(s) for i, s in enumerate(out) if i % 2])
        sz = sz1 + sz2 + 3
        if sz < CON_WD:
            if len(out) % 2:
                out.append('')
            out = [f"{a:<{sz // 2}} | {b:<{sz // 2}}" for (a, b) in
                   [out[i:i + 2] for i in range(0, len(out), 2)]]
        else:
            sz = max(sz1, sz2) + 4
            out = [f"{s:<{sz}}" for s in out]
        return ['', f"{' Options: ':-^{sz}}", *out]

    @classmethod
    def getMap(cls) -> str:
        return (f"-map 0:v{'' if cls.vid_strm == 'all' else f':{cls.vid_strm}'} "
                f"-map 0:a{'' if cls.aud_strm == 'all' else f':{cls.aud_strm}'}? "
                f"-map 0:s{'' if cls.sub_strm == 'all' else f':{cls.sub_strm}'}?")


class _BuildCmd:
    pth_in: Path
    pth_out: Path
    vid_dur: float
    cmd: O[str]

    def __init__(self, pth_in: Path):
        self.pth_in = pth_in
        vidcmd = self.videoCmd()
        audcmd = self.audioCmd()
        if vidcmd or audcmd or [_Opt.vid_strm, _Opt.aud_strm, _Opt.sub_strm].count('all') < 3:
            timecmd = self.timeCmd()
            if self.pth_out.suffix == '.webm':
                self.cmd = (f'ffmpeg -hide_banner -y -i "{pth_in}" '
                            f'{"-hwaccel_output_format cuda" if CONV_NVENC else ""} '
                            f'-movflags faststart {vidcmd} "{self.pth_out}"; {timecmd}')
            else:
                self.cmd = (f'ffmpeg -hide_banner -y -i "{pth_in}" -movflags '
                            f'faststart {_Opt.getMap()} -c copy {vidcmd} '
                            f'{audcmd} -c:s ssa "{self.pth_out}"; {timecmd}')
        elif pth_in.suffix != self.pth_out.suffix:
            timecmd = self.timeCmd()
            self.cmd = (f'ffmpeg -hide_banner -y -i "{pth_in}" -c copy '
                        f"{'' if self.pth_out.suffix == '.webm' else '-c:s ssa'} "
                        f'-movflags faststart "{self.pth_out}"; {timecmd}')
        else:
            self.cmd = None

    def videoCmd(self) -> str:
        # get video info
        vidinfo: str = run(['ffprobe', '-i', self.pth_in, '-v', 'error', '-select_streams',
                            f"v{'' if _Opt.vid_strm == 'all' else f':{_Opt.vid_strm}'}",
                            '-show_entries', 'format=duration:stream=codec_name,height,width',
                            '-of', 'default=nw=1'],
                           capture_output=True,
                           text=True).stdout
        codec = re_search(r'codec_name=(.+)', vidinfo).group(1).lower()
        v_ht = int(re_search(r'height=(.+)', vidinfo).group(1))
        v_wd = int(re_search(r'width=(.+)', vidinfo).group(1))
        self.vid_dur = float(re_search(r'duration=(.+)', vidinfo).group(1))
        # get crop
        cropinfo: str = run(['ffmpeg', '-hide_banner', '-i', self.pth_in, '-vframes', '10',
                             '-vf', 'cropdetect', '-f', 'null', '-'],
                            capture_output=True,
                            text=True,
                            cwd=self.pth_in.parent).stderr
        try:
            crop = re_findall(r'crop=.+', cropinfo)[-1]
            cw, ch, cx, cy = re_findall(r'\d+', crop)
            if '-' in crop or (cw - cx) < (v_wd / 3) or (ch - cy) < (v_ht / 3):
                crop = str()
            else:
                crop = f"-vf {crop}"
        except:
            crop = str()
        # build command
        hevcpth = self.pth_in.with_name(f"[HEVC-AAC] {self.pth_in.stem}.mkv")
        vp9pth = self.pth_in.with_name(f"[VP9-OPUS] {self.pth_in.stem}.webm")
        if 'hevc' in codec or 'vp9' in codec or 'vp8' in codec:
            self.pth_out = hevcpth if 'hevc' in codec else vp9pth
            return crop
        elif CONV_NVENC and _Opt.output != '.webm' and self.vid_dur >= _Opt.playtime:
            self.pth_out = hevcpth
            return f'{crop} -c:v hevc_nvenc -preset slow'
        else:
            # get crf from v_ht
            crf = 7
            for ht, val in CRF_VALS:
                if ht >= v_ht:
                    crf = val
                    break
            if _Opt.output != '.webm' and self.vid_dur >= _Opt.playtime:
                self.pth_out = hevcpth
                return f'{crop} -c:v libx265 -crf {crf} -preset slow'
            else:
                self.pth_out = vp9pth
                return f'{crop} -c:v vp9 -b:v 0 -crf {crf}'

    def audioCmd(self) -> str:
        if self.pth_out.suffix == '.webm':
            return str()
        # get audio info
        audinfo: str = run(['ffprobe', self.pth_in, '-v', 'error', '-select_streams',
                            f"a{'' if _Opt.aud_strm == 'all' else f':{_Opt.aud_strm}'}",
                            '-show_entries', 'stream=codec_name,channels', '-of', 'default=nw=1'],
                           capture_output=True,
                           text=True).stdout
        if not audinfo:
            return str()
        codec = re_search(r'codec_name=(.+)', audinfo).group(1).lower()
        chnls = int(re_search(r'channels=(.+)', audinfo).group(1))
        # check if audio already compressed
        if 'aac' in codec or 'ac3' in codec or 'opus' in codec or 'vorbis' in codec:
            return str()
        # build command
        return f'-c:a aac -b:a {chnls * 64}k'

    def timeCmd(self) -> str:
        # retrieve and format file create/modify time
        st = self.pth_in.stat()
        dt = datetime.fromtimestamp
        frmt = "%A, %B %d, %Y %I:%M:%S %p"
        mt = dt(st.st_mtime).strftime(frmt)
        ct = dt(st.st_ctime).strftime(frmt)
        # build command
        return (f'$o = Get-Item -LiteralPath "{self.pth_out}"; '
                f'$o.LastWriteTime = "{mt}"; '
                f'$o.CreationTime = "{ct}"')


class ConvertVideo:
    """Convert and compress video files with specified extensions (from config.ini) within this folder (and optionally its subfolders) to HEVC/AAC or VP9/OPUS.

    3rd-party Requirements
    ----------
    FFmpeg (https://www.ffmpeg.org/)
    """

    topfol: Path
    files: list[Path]
    results: dict[str, int]
    finct: int
    totct: int
    dSize: int = 0

    def __init__(self, top_path: str):
        """\
        Parameters
        ----------
        top_path (str): The path to either a directory to be searched or a video file
        """

        # resize window
        run(['powershell', '-command', CON_SZ_CMD])
        # init vars
        fpath = Path(top_path).resolve()
        dorun = _Opt.getInput(fpath)
        if not dorun:
            return
        elif fpath.is_dir():
            self.topfol = fpath
            srch = self.topfol.rglob if _Opt.recurse else self.topfol.glob
            self.files = [f for f in srch('*.*')
                          if f.suffix in CONV_FTYPES
                          and '[HEVC-AAC]' not in f.stem
                          and '[VP9-OPUS]' not in f.stem]
        else:
            self.topfol = fpath.parent
            self.files = [fpath]
        self.run(fpath)

    def run(self, fpath: Path):
        def formatTxt(*args: str) -> str:
            return '\n'.join([f'{f" {s} " if s else s:=^{CON_WD}}'
                              for s in ('', *args, '')])
        # init vars
        t_start = datetime.now()
        self.results = dict(err=0, fail=0)
        self.finct = 1
        self.totct = len(self.files)
        print(formatTxt(f"COMPRESSING/CONVERTING {self.totct} ITEMS",
                        f"({fpath})",
                        *_Opt.getInfo()))
        # run
        with ThreadPoolExecutor(max_workers=int(_Opt.thread_ct)) as ex:
            ex.map(self.process, self.files)
        # stop
        t_end = datetime.now()
        h, m, s = str(t_end - t_start).split(':')
        t_elapsed = ' '.join((f"{h:0>2}h", f"{m:0>2}m", f"{float(s):05.02f}s"))
        # cleanup
        msg = (f"Processed {self.totct} items:\n"
               f"  {self.results['fail']} failed\n"
               f"  {self.results['err']} errors\n"
               f"Time elapsed: {t_elapsed}\n"
               f"Result: {self.dSize:.2f}MB {'reduction' if self.dSize < 0 else 'increase'} in size")
        Mbox.showinfo(title='Processing Complete',
                      message=msg)
        run(['powershell', 'clear'])

    def process(self, pth_in: Path) -> None:
        def getPath() -> str:
            fill = TextWrapper(width=CON_WD,
                               subsequent_indent='    ').fill
            namestr = fill(f'INPUT: "{pth_in.name}"')
            if _Opt.recurse:
                ffol = str(pth_in.parent.relative_to(self.topfol))
                if ffol != '.':
                    ffol = f'.\\{ffol}'
                folstr = fill(f'DIR: "{ffol}"')
                return f'{folstr}\n{namestr}'
            else:
                return namestr

        def getResults() -> str:
            if pth_out.exists() and pth_out.stat().st_size >= 100 and not returncode:
                sz_in = float(pth_in.stat().st_size)
                sz_out = float(pth_out.stat().st_size)
                sz_dif = (sz_out - sz_in) / (1024**2)
                self.dSize += sz_dif
                sz_difp = (1.0 - sz_out / sz_in) * 100
                if sz_dif < 0:
                    resstr = ("COMPRESSED FILE BY "
                              f"{sz_difp:02.2f}% ({sz_dif:+02.2f}MB)")
                    if _Opt.overwrite:
                        err = RunCmd(
                            f'powershell Move-Item -LiteralPath "{pth_out}" "{pth_out.with_stem(pth_in.stem)}" -Force',
                            console='new',
                            visibility='hide',
                            capture_output=True).communicate()[1]
                        if err:
                            resstr += "\n    COULDN'T REMOVE ORIGINAL FILE"
                elif _Opt.keepfail:
                    self.results['fail'] += 1
                    resstr = ("CONVERSION SUCCESSFUL;\n"
                              f"   COMPRESSION INEFFECTIVE ({sz_dif:+02.2f}MB)")
                    if _Opt.overwrite:
                        err = RunCmd(
                            f'powershell Move-Item -LiteralPath "{pth_out}" "{pth_out.with_stem(pth_in.stem)}" -Force',
                            console='new',
                            visibility='hide',
                            capture_output=True).communicate()[1]
                        if err:
                            resstr += "\n    COULDN'T REMOVE ORIGINAL FILE"
                else:
                    self.results['fail'] += 1
                    resstr = f"PROCESSING INEFFECTIVE ({sz_dif:+02.2f}MB)"
                    pth_out.unlink(missing_ok=True)
            else:
                self.results['err'] += 1
                errstr = (f"returncode <{returncode}>" if returncode
                          else "file could not be processed" if not pth_out.exists()
                          else "file processing failed" if pth_out.stat().st_size < 100
                          else "unknown error")
                resstr = f"ERROR: {errstr}"
                pth_out.unlink(missing_ok=True)
                logging.exception(f'{"#" * 10}\n'
                                  f'{pathstr}\n'
                                  f'>> {resstr}\n')
            return resstr

        info = _BuildCmd(pth_in)
        pth_out, cmd = info.pth_out, info.cmd
        if cmd:
            returncode = RunCmd(['powershell', '-command', cmd],
                                console='new',
                                visibility='min').wait()
        # print results
        divstr = f"{f' Item {self.finct} of {self.totct} ':-^{CON_WD}}"
        self.finct += 1
        pathstr = getPath()
        if not cmd:
            resstr = "ALREADY COMPRESSED/CONVERTED"
        else:
            resstr = getResults()
        print(f'{divstr}\n'
              f'[{str(datetime.now())[5:19]}]\n'
              f'{pathstr}\n'
              f'>> {resstr}\n')
