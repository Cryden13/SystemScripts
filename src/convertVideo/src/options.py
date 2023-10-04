from subprocess import run

from winnotify import InputDialog as InDlg

from ....lib.variables import *


class Options:
    output: str = ''
    aud_strm: str = list(CONV_AUD_LANGS)[0]
    sub_strm: str = list(CONV_SUB_LANGS)[0]
    overwrite: bool = CONV_OVERWRITE
    do_scale: bool = CONV_DO_SCALE
    do_crop: bool = CONV_DO_CROP
    keep_fail: bool = CONV_KEEP_FAIL
    keep_error: bool = CONV_KEEP_ERROR
    isdir: bool = False
    recurse: bool = CONV_RECURSE
    playtime: str = CONV_CUTOFF
    thread_ct: int = CONV_THREADS

    @classmethod
    def getInput(cls, fpath: Path) -> bool:
        fields = [
            ('Audio stream', InDlg.ChWgt.combobox(options=['all', *list(CONV_AUD_LANGS), *[str(i) for i in range(CONV_STREAMS)]],
                                                  default=cls.aud_strm)),
            ('Subtitle stream', InDlg.ChWgt.combobox(options=['all', 'remove', *list(CONV_SUB_LANGS), *[str(i) for i in range(CONV_STREAMS)]],
                                                     default=cls.sub_strm)),
            ('Overwrite original', InDlg.ChWgt.checkbox(default=cls.overwrite)),
            ('Scale to 720p', InDlg.ChWgt.checkbox(default=cls.do_scale)),
            ('Crop blackspace', InDlg.ChWgt.checkbox(default=cls.do_crop)),
            ('Keep compression failures', InDlg.ChWgt.checkbox(default=cls.keep_fail)),
            ('Keep errored files', InDlg.ChWgt.checkbox(default=cls.keep_error))
        ]
        if fpath.is_dir():
            cls.isdir = True
            fields.insert(0, ('Output format', InDlg.ChWgt.combobox(options=['auto', '.mkv', '.mp4', '.webm'],
                                                                    default='auto')))
            fields += [
                ('Recurse folders', InDlg.ChWgt.checkbox(default=cls.recurse)),
                ('Webm cutoff (sec)', InDlg.ChWgt.spinbox(from_=0,
                                                          to=3600,
                                                          default=cls.playtime)),
                ('Thread count', InDlg.ChWgt.spinbox(from_=1,
                                                     to=(3 if CONV_NVENC else 20),
                                                     default=cls.thread_ct))
            ]
            msg = (f"{fpath}\n\n"
                   f"Compress/Convert {', '.join(CONV_FTYPES)} files within this directory.")
        else:
            dur: str = run(['ffprobe', '-v', 'error', '-show_entries',
                            'format=duration', '-of', 'csv=p=0', '-i', fpath],
                           capture_output=True,
                           text=True).stdout
            fields.insert(0, ('Output format', InDlg.ChWgt.combobox(options=['.mkv', '.mp4', '.webm'],
                                                                    default=('.mkv' if float(dur) >= cls.playtime else '.webm'))))
            msg = f"{fpath.name}\n\nCompress/Convert this file."
        ans = InDlg.multiinput(
            title="Compress/Convert Video - Options",
            message=f"{msg}\n",
            input_fields=fields,
            playsound='alert',
            icon=CONV_ICON
        )
        if ans:
            cls.output = ans['Output format']
            cls.aud_strm = ans['Audio stream']
            cls.sub_strm = ans['Subtitle stream']
            cls.overwrite = ans['Overwrite original']
            cls.do_scale = ans['Scale to 720p']
            cls.do_crop = ans['Crop blackspace']
            cls.keep_fail = ans['Keep compression failures']
            cls.keep_error = ans['Keep errored files']
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
            f"Audio stream: {cls.aud_strm.upper()}",
            f"Subtitle stream: {cls.sub_strm.upper()}",
            f"Overwrite original: {'YES' if cls.overwrite else 'NO'}",
            f"Scale to 720p: {'YES' if cls.do_scale else 'NO'}",
            f"Crop blackspace: {'YES' if cls.do_crop else 'NO'}",
            f"Keep failures: {'YES' if cls.keep_fail else 'NO'}",
            f"Keep errors: {'YES' if cls.keep_error else 'NO'}"
        ]
        if cls.isdir:
            out.insert(0, f"Running threads: {cls.thread_ct}")
            out += [f"Recurse folders: {'YES' if cls.recurse else 'NO'}"]
            if cls.output == 'auto':
                out.append(f"Playtime cutoff: {cls.playtime}s")
        if CONV_CON_WD > 53:
            if len(out) % 2:
                out.append('')
            out = [f"{a:<24} | {b:<24}" for (a, b) in
                   [out[i:i + 2] for i in range(0, len(out), 2)]]
        else:
            out = [f"{s:<24}" for s in out]
        return ['', f"{' Options: ':-^{51}}", *out]
