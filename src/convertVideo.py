from concurrent.futures import ThreadPoolExecutor
from typing import Optional as O
from textwrap import TextWrapper
from datetime import datetime
from subprocess import run
from commandline import *
from pathlib import Path
import logging

from re import (
    findall as re_findall,
    search as re_search
)

from ..lib.variables import *

from winnotify import (
    InputDialog as InDlg,
    Messagebox as Mbox,
    PlaySound
)


class _Opt:
    thread_ct: int = CONV_THREADS
    output: str = ''
    vid_strm: str = 'all'
    aud_strm: str = 'all'
    sub_strm: str = 'all'
    overwrite: bool = False
    do_scale: bool = False
    isdir: bool = False
    keepfail: bool = False
    recurse: bool = False
    playtime: str = CONV_CUTOFF

    @classmethod
    def getInput(cls, fpath: Path) -> bool:
        fields = [
            ('Video stream', InDlg.ChWgt.combobox(options=['all', *[str(i) for i in range(CONV_STREAMS)]],
                                                  default=cls.vid_strm)),
            ('Audio stream', InDlg.ChWgt.combobox(options=['all', *[str(i) for i in range(CONV_STREAMS)]],
                                                  default=cls.aud_strm)),
            ('Subtitle stream', InDlg.ChWgt.combobox(options=['all', 'none', *[str(i) for i in range(CONV_STREAMS)]],
                                                     default=cls.sub_strm)),
            ('Overwrite original', InDlg.ChWgt.checkbox(default=cls.overwrite)),
            ('Scale to 720p', InDlg.ChWgt.checkbox(default=cls.do_scale)),
            ('Keep failures', InDlg.ChWgt.checkbox(default=cls.keepfail))
        ]
        if fpath.is_dir():
            cls.isdir = True
            fields.insert(0, ('Output format', InDlg.ChWgt.combobox(options=['choose', '.mkv', '.mp4', '.webm'],
                                                                    default='choose')))
            fields += [
                ('Recurse folders', InDlg.ChWgt.checkbox(default=cls.recurse)),
                ('Webm cutoff (sec)', InDlg.ChWgt.spinbox(from_=0,
                                                          to=3600,
                                                          default=cls.playtime)),
                ('Thread count', InDlg.ChWgt.spinbox(from_=1,
                                                     to=(3 if CONV_NVENC else 20),
                                                     default=cls.thread_ct))
            ]
            msg = (f"<{fpath}>\n"
                   f"Compress/Convert {', '.join(CONV_FTYPES)} files within this directory.")
        else:
            dur: str = run(['ffprobe', '-v', 'error', '-show_entries',
                            'format=duration', '-of', 'csv=p=0', '-i', fpath],
                           capture_output=True,
                           text=True).stdout
            fields.insert(0, ('Output format', InDlg.ChWgt.combobox(options=['.mkv', '.mp4', '.webm'],
                                                                    default=('.mkv' if float(dur) >= cls.playtime else '.webm'))))
            msg = f"<{fpath.name}>\nCompress/Convert this file."
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
            cls.do_scale = ans['Scale to 720p']
            cls.keepfail = ans['Keep failures']
            if cls.isdir:
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
            f"Overwrite original: {'yes' if cls.overwrite else 'no'}",
            f"Scale to 720p: {'yes' if cls.do_scale else 'no'}",
            f"Keep failures: {'yes' if cls.keepfail else 'no'}"
        ]
        if cls.isdir:
            out.insert(0, f"Running threads: {cls.thread_ct}")
            out += [f"Recurse folders: {'yes' if cls.recurse else 'no'}"]
            if cls.output == 'choose':
                out.append(f"Playtime cutoff: {cls.playtime}s")
        if CON_WD > 53:
            if len(out) % 2:
                out.append('')
            out = [f"{a:<24} | {b:<24}" for (a, b) in
                   [out[i:i + 2] for i in range(0, len(out), 2)]]
        else:
            out = [f"{s:<24}" for s in out]
        return ['', f"{' Options: ':-^{51}}", *out]


class _DataContainer:
    def __init__(self, pth_in: Path):
        self.vid = self._Vid(pth_in)
        self.aud = self._Aud(pth_in)
        self.sub = self._Sub(pth_in)

    class _Vid:
        def __init__(self, pth_in: Path):
            raw: str = run(['ffprobe', '-i', pth_in, '-v', 'error', '-select_streams', 'v:0',
                            '-show_entries', 'format=duration:stream=codec_name,height,width',
                            '-of', 'default=nw=1'],
                           capture_output=True,
                           text=True).stdout
            self.codec = re_search(r'codec_name=(.+)', raw).group(1).lower()
            self.ht = int(re_search(r'height=(.+)', raw).group(1))
            self.wd = int(re_search(r'width=(.+)', raw).group(1))
            self.dur = float(re_search(r'duration=(.+)', raw).group(1))
            # get crop
            cropinfo: str = run(['ffmpeg', '-hide_banner', '-ss', f'{self.dur//2}', '-i', pth_in,
                                 '-t', '2', '-vsync', 'vfr', '-vf', 'cropdetect', '-f', 'null', '-'],
                                capture_output=True,
                                text=True,
                                cwd=pth_in.parent).stderr
            croplst = list()
            try:
                cropstr = re_findall(r'crop=.+', cropinfo)[-1]
                cw, ch, cx, cy = [int(n) for n in re_findall(r'\d+', cropstr)]
                if cw < self.wd or ch < self.ht:
                    if '-' not in cropstr and ((cw - cx) > (self.wd / 3) or (ch - cy) > (self.ht / 3)):
                        croplst.append(cropstr)
            except:
                pass
            if _Opt.do_scale:
                d_wd = self.wd - 1280
                d_ht = self.ht - 720
                if self.wd > 1280 and d_wd > d_ht:
                    croplst.append('scale=1280:-1')
                elif self.ht > 720:
                    croplst.append('scale=-1:720')
            if croplst:
                self.crop = f"-filter:v:1 {','.join(croplst)}"
            else:
                self.crop = ''

    class _Aud:
        def __init__(self, pth_in: Path):
            self.raw: str = run(['ffprobe', pth_in, '-v', 'error', '-select_streams',
                                 f"a{'' if _Opt.aud_strm == 'all' else f':{_Opt.aud_strm}'}",
                                 '-show_entries', 'stream=codec_name,channels', '-of', 'default=nw=1'],
                                capture_output=True,
                                text=True).stdout
            if self.raw:
                self.codec = re_search(
                    r'codec_name=(.+)', self.raw).group(1).lower()
                self.chnls = int(
                    re_search(r'channels=(.+)', self.raw).group(1)) * 64

    class _Sub:
        def __init__(self, pth_in: Path):
            if _Opt.sub_strm == 'none':
                self.codec = ''
            else:
                self.codec: str = run(['ffprobe', pth_in, '-v', 'error', '-select_streams',
                                       f"s{'' if _Opt.sub_strm == 'all' else f':{_Opt.sub_strm}'}",
                                       '-show_entries', 'stream=codec_name', '-of', 'csv=p=0'],
                                      capture_output=True,
                                      text=True).stdout


class _BuildCmd:
    pth_in: Path
    todo: dict[str, list[str]]
    pth_out: Path
    cmd: O[str]

    def __init__(self, pth_in: Path):
        self.pth_in = pth_in
        self.todo = dict(V=list(), A=list(), S=list())
        self.data = _DataContainer(pth_in)
        vid_cmd = self.videoCmd()
        aud_cmd = self.audioCmd()
        sub_cmd = self.subCmd()
        todo = [f"{k}{''.join(v)}" for k, v in self.todo.items() if v]
        namecmd = f'$host.UI.RawUI.WindowTitle = "[{"|".join(todo)}] {pth_in.name}"'
        if vid_cmd or aud_cmd or sub_cmd or pth_in.suffix != self.pth_out.suffix or [_Opt.vid_strm, _Opt.aud_strm, _Opt.sub_strm].count('all') < 3:
            time_cmd = self.timeCmd()
            ffmpeg_cmd = (f'ffmpeg -hide_banner -y -i "{pth_in}" -i "{pth_in}" '
                          f'-movflags faststart -map 0:v:0 -map 1:v {vid_cmd} '
                          f'-map 1:a? {aud_cmd} {sub_cmd} -filter:v:0 thumbnail,scale=360:-1,trim=end_frame=1 '
                          f'-c:v:0 mjpeg -disposition:0 attached_pic '
                          f'"{self.pth_out}"')
            print(ffmpeg_cmd)
            self.cmd = f'{namecmd}; {ffmpeg_cmd}; {time_cmd}'
        else:
            self.cmd = None

    def videoCmd(self) -> str:
        # get relevant data
        v_data = self.data.vid

        # build command
        def getCRF():
            crf = 7
            for ht, val in CRF_VALS:
                if ht >= v_data.ht:
                    crf = val
                    break
            return crf

        def convHevc():
            if self.pth_out.suffix == self.pth_in.suffix and 'hevc' in v_data.codec:
                # already converted
                if v_data.crop:
                    # need cropping
                    self.todo['V'].append('c')
                    return v_data.crop
                else:
                    return '-c:v copy'
            else:
                # needs conversion, may need cropping
                self.todo['V'].append('c')
                codec = ('hevc_nvenc' if CONV_NVENC else
                         f'libx265 -crf {getCRF()}')
                return f'-c:v {codec} -preset slow {v_data.crop}'

        def convVp9():
            if self.pth_out.suffix == self.pth_in.suffix and 'vp9' in v_data.codec:
                # already converted
                if v_data.crop:
                    # needs cropping
                    self.todo['V'].append('c')
                    return v_data.crop
                else:
                    return '-c:v copy'
            else:
                # needs conversion, may need cropping
                self.todo['V'].append('c')
                return f'-c:v vp9 -b:v 0 -crf {getCRF()} {v_data.crop}'

        # OPTION: CHOOSE
        if _Opt.output == 'choose':
            # create paths
            hevcpth = self.pth_in.with_name(
                f"[HEVC-AAC] {self.pth_in.stem}"
                f"{'.mkv' if self.data.sub.codec else '.mp4'}")
            vp9pth = self.pth_in.with_name(
                f"[VP9-OPUS] {self.pth_in.stem}.webm")
            # check length
            if v_data.dur >= _Opt.playtime:
                # convert to HEVC
                self.pth_out = hevcpth
                return convHevc()
            else:
                # convert to VP9
                self.pth_out = vp9pth
                return convVp9()
        # OPTION: WEBM
        elif _Opt.output == '.webm':
            self.pth_out = self.pth_in.with_name(
                f"[VP9-OPUS] {self.pth_in.stem}.webm")
            return convVp9()
        # OPTION: MKV OR MP4
        else:
            self.pth_out = self.pth_in.with_name(
                f"[HEVC-AAC] {self.pth_in.stem}{_Opt.output}")
            return convHevc()

    def audioCmd(self) -> str:
        # get relevant data
        a_data = self.data.aud
        # get audio info
        if not a_data.raw:
            return str()
        # check if audio already compressed
        if ('aac' in a_data.codec and (self.pth_out.suffix == '.mkv' or self.pth_out.suffix == '.mp4')) or ('opus' in a_data.codec and self.pth_out.suffix == '.webm'):
            return '-c:a copy'
        # build command
        else:
            self.todo['A'].append('c')
            codec = 'libopus' if self.pth_out.suffix == '.webm' else 'aac'
            return f'-c:a {codec} -b:a {a_data.chnls}k'

    def subCmd(self) -> str:
        if not self.data.sub.codec:
            return str()
        else:
            self.todo['S'].append('c')
            if self.pth_out.suffix == '.mp4':
                return '-map 1:s -c:s mov_text'
            elif self.pth_out.suffix == '.mkv':
                return '-map 1:s -c:s ssa'
            else:
                return '-map -1:s?'

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
        run(['powershell', '-command',
             f'$host.UI.RawUI.WindowTitle="Compress/Convert Video"; {CON_SZ_CMD}'])
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
        print(formatTxt(f"PROCESSING {self.totct} ITEMS",
                        f"({fpath})",
                        *_Opt.getInfo()))
        # run
        # with ThreadPoolExecutor(max_workers=int(_Opt.thread_ct)) as ex:
        #     ex.map(self.process, self.files)
        self.process(self.files[0])
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
                ffol = '.\\' if ffol == '.' else f'.\\{ffol}'
                folstr = fill(f'DIR: "{ffol}"')
                return f'{folstr}\n{namestr}'
            else:
                return namestr

        def getResults() -> str:
            err_chk = run(f'ffmpeg -hide_banner -v error -i "{pth_out}" -map 0:1 -f null -',
                          capture_output=True,
                          text=True,
                          cwd=pth_out.parent).stderr
            if pth_out.exists() and not err_chk and not returncode:
                sz_in = float(pth_in.stat().st_size / 1024**2)
                sz_out = float(pth_out.stat().st_size / 1024**2)
                sz_dif = (sz_out - sz_in)
                sz_comp = f"({sz_in:02.2f} -> {sz_out:02.2f} :: {sz_dif:+02.2f}MB)"
                sz_difp = (1.0 - sz_out / sz_in) * 100
                if sz_dif < 0:
                    self.dSize += sz_dif
                    resstr = ("COMPRESSED FILE BY "
                              f"{sz_difp:02.2f}% {sz_comp}")
                    if _Opt.overwrite:
                        try:
                            pth_in.unlink()
                            pth_out.rename(pth_out.with_stem(pth_in.stem))
                        finally:
                            if pth_out.exists():
                                resstr += "\n    COULDN'T REMOVE ORIGINAL FILE"
                elif _Opt.keepfail:
                    self.dSize += sz_dif
                    self.results['fail'] += 1
                    resstr = ("CONVERSION SUCCESSFUL;\n"
                              f"   COMPRESSION INEFFECTIVE {sz_comp}")
                    if _Opt.overwrite:
                        try:
                            pth_in.unlink()
                            pth_out.rename(pth_out.with_stem(pth_in.stem))
                        finally:
                            if pth_out.exists():
                                resstr += "\n    COULDN'T REMOVE ORIGINAL FILE"
                else:
                    self.results['fail'] += 1
                    resstr = f"PROCESSING INEFFECTIVE {sz_comp}"
                    pth_out.unlink(missing_ok=True)
            else:
                self.results['err'] += 1
                errstr = (f"returncode <{returncode}>\n== TRACEBACK ============\n{err_chk}\n{'='*25}" if err_chk
                          else f"returncode <{returncode}>\n== TRACEBACK ============\n{err}\n{'='*25}" if err
                          else f"returncode <{returncode}>" if returncode
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
            cmd += '; pause'
            returncode = RunCmd(['powershell', '-command', cmd],
                                console='new',
                                visibility='min').wait()
            if returncode:
                if returncode == 3221225786:
                    err = 'User closed the window'
                else:
                    _, err = RunCmd(['powershell', '-command', cmd],
                                    console='new',
                                    capture_output=True,
                                    visibility='hide').communicate()
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
