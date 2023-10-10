from typing import TYPE_CHECKING
from datetime import datetime
import logging

from ....lib.variables import *
from .dataContainer import DataContainer

if TYPE_CHECKING:
    from .options import Options


class BuildCmd:
    pth_in: Path
    Opt: "Options"
    todo: dict[str, list[str]]
    # V: c=convert, x=crop
    # A/S: m=add metadata, l=select by language, s=select stream, c=convert
    pth_out: Path
    do_vid = True
    do_aud = True
    do_sub = True
    ffmpeg_cmd = str()
    cmd: O[str]

    def __init__(self, pth_in: Path, options: "Options"):
        self.pth_in = pth_in
        self.Opt = options
        self.todo = dict(V=list(), A=list(), S=list())
        self.data = DataContainer(pth_in, self.Opt)
        vid_cmd = self.videoCmd()
        aud_cmd = self.audioCmd()
        sub_cmd = self.subCmd()
        todo = [f"{k}{''.join(v)}" for k, v in self.todo.items() if v]
        if (
            self.do_vid
            or self.do_aud
            or self.do_sub
            or pth_in.suffix != self.pth_out.suffix
        ):
            title_cmd = (
                f'$host.UI.RawUI.WindowTitle = "[{"|".join(todo)}] {pth_in.name}"'
            )
            time_cmd = self.timeCmd()
            self.ffmpeg_cmd = (
                f'ffmpeg -hide_banner -y -i "{pth_in}" '
                f"-movflags faststart "
                f"{vid_cmd} {aud_cmd} {sub_cmd} "
                f'{self.Opt.add_params} "{self.pth_out}"'
            )
            # logging.debug(self.ffmpeg_cmd)
            self.cmd = f"{title_cmd}; {self.ffmpeg_cmd}; {time_cmd}"
        else:
            self.cmd = None

    def videoCmd(self) -> str:
        # get relevant data
        v_data = self.data.vid

        # build command
        def getCRF():
            crf = 7
            for ht, val in CONV_CRF_VALS:
                if ht >= v_data.ht:
                    crf = val
                    break
            return crf

        def convHevc():
            if (
                self.pth_out.suffix == self.pth_in.suffix
                and "hevc" in v_data.codec
                and not v_data.crop
            ):
                # already converted
                self.do_vid = False
                return "-map 0:v -c:v copy"
            # needs conversion
            self.todo["V"].append("c")
            if v_data.crop:
                # need cropping
                self.todo["V"].append("x")
            codec = "hevc_nvenc" if CONV_NVENC else f"libx265 -crf {getCRF()}"
            if self.pth_out.suffix == ".mp4":
                return (
                    "-filter_complex [0:v]thumbnail,trim=end_frame=1,scale=360:-1[thumb] "
                    f"-map 0:v -c:v:0 {codec} -preset slow {v_data.crop} "
                    "-map [thumb] -c:v:1 mjpeg -disposition:v:1 attached_pic"
                )
            else:
                return f"-map 0:v -c:v {codec} -preset slow {v_data.crop}"

        def convVp9():
            if (
                self.pth_out.suffix == self.pth_in.suffix
                and "vp9" in v_data.codec
                and not v_data.crop
            ):
                self.do_vid = False
                return "-map 0:v -c:v copy"
            else:
                # needs conversion
                self.todo["V"].append("c")
                if v_data.crop:
                    # needs cropping
                    self.todo["V"].append("x")
                return f"-map 0:v -c:v vp9 -b:v 0 -crf {getCRF()} {v_data.crop}"

        # create paths
        hevcpth = self.pth_in.with_name(
            f"[HEVC-AAC] {self.pth_in.stem}"
            f"{self.Opt.output if self.Opt.output != 'auto' else '.mkv' if self.data.sub.streams else '.mp4'}"
        )
        vp9pth = self.pth_in.with_name(f"[VP9-OPUS] {self.pth_in.stem}.webm")
        # OPTION: DON'T CONVERT
        if self.Opt.conv_vid == False:
            self.pth_out = self.pth_in.with_stem(f"[PROCESSED] {self.pth_in.stem}")
            if v_data.crop:
                self.todo["V"].append("x")
                return f"-map 0:v {v_data.crop}"
            else:
                self.do_vid = False
                return "-map 0:v -c:v copy"
        # OPTION: AUTO
        if self.Opt.output == "auto":
            # check length
            if v_data.dur >= self.Opt.playtime:
                # convert to HEVC
                self.pth_out = hevcpth
                return convHevc()
            else:
                # convert to VP9
                self.pth_out = vp9pth
                return convVp9()
        # OPTION: WEBM
        elif self.Opt.output == ".webm":
            self.pth_out = vp9pth
            return convVp9()
        # OPTION: MKV OR MP4
        else:
            self.pth_out = hevcpth
            return convHevc()

    def audioCmd(self) -> str:
        # get relevant data
        a_data = self.data.aud
        if a_data.add_metadata:
            self.todo["A"].append("m")
            map_str = (
                f"-map 0:a:{self.Opt.aud_strm}? -metadata:s:a:0 language={a_data.add_metadata} "
                f"-metadata:s:a:0 title={CONV_AUD_LANGS.get(a_data.add_metadata)} "
                f"-metadata:s:a:0 handler_name={CONV_AUD_LANGS.get(a_data.add_metadata)}"
            )
        elif self.Opt.aud_strm in CONV_AUD_LANGS and len(a_data.lang_match) < len(
            a_data.strm_list
        ):
            self.todo["A"].append("l")
            map_str = f"-map 0:a:m:language:{self.Opt.aud_strm}?"
        elif self.Opt.aud_strm.isnumeric() and len(a_data.strm_list) > 1:
            self.todo["A"].append("s")
            map_str = f"-map 0:a:{self.Opt.aud_strm}?"
        else:
            map_str = "-map 0:a?"
        # get audio info
        if (
            not self.Opt.conv_aud
            or not a_data.streams
            or (
                self.pth_out.suffix in [".mkv", ".mp4"]
                and a_data.streams.count("aac") == len(a_data.strm_list)
            )
            or (
                self.pth_out.suffix == ".webm"
                and a_data.streams.count("opus") == len(a_data.strm_list)
            )
        ):
            # no audio or all streams are already converted
            if map_str == "-map 0:a?":
                self.do_aud = False
            return f"{map_str} -c:a copy"
        # build command
        else:
            self.todo["A"].append("c")
            codec = "libopus" if self.pth_out.suffix == ".webm" else "aac"
            return f"{map_str} -c:a {codec} -b:a {a_data.chnls}k"

    def subCmd(self) -> str:
        # get relevant data
        s_data = self.data.sub
        if s_data.add_metadata:
            self.todo["S"].append("m")
            map_str = (
                f"-map 0:s:{self.Opt.sub_strm}? -metadata:s:s:0 language={s_data.add_metadata} "
                f"-metadata:s:s:0 title={CONV_SUB_LANGS.get(s_data.add_metadata)} "
                f"-metadata:s:s:0 handler_name={CONV_SUB_LANGS.get(s_data.add_metadata)}"
            )
        elif self.Opt.sub_strm in CONV_SUB_LANGS and len(s_data.lang_match) < len(
            s_data.strm_list
        ):
            self.todo["S"].append("l")
            map_str = f"-map 0:s:m:language:{self.Opt.sub_strm}?"
        elif self.Opt.sub_strm.isnumeric() and len(s_data.strm_list) > 1:
            self.todo["S"].append("s")
            map_str = f"-map 0:s:{self.Opt.sub_strm}?"
        else:
            map_str = "-map 0:s?"
        if (
            not self.Opt.conv_sub
            or not s_data.streams
            or s_data.force_copy
            or (
                self.pth_out.suffix == ".mkv"
                and s_data.streams.count("ass") == len(s_data.strm_list)
            )
            or (
                self.pth_out.suffix == ".mp4"
                and s_data.streams.count("mov_text") == len(s_data.strm_list)
            )
        ):
            # no subs or image based or already converted
            if map_str == "-map 0:s?":
                self.do_sub = False
            return f"{map_str} -c:s copy"
        else:
            self.todo["S"].append("c")
            if self.pth_out.suffix == ".mp4":
                return f"{map_str} -c:s mov_text"
            elif self.pth_out.suffix == ".mkv":
                return f"{map_str} -c:s ass"
            else:
                if map_str == "-map 0:s?":
                    self.do_sub = False
                return map_str

    def timeCmd(self) -> str:
        # retrieve and format file create/modify time
        st = self.pth_in.stat()
        dt = datetime.fromtimestamp
        frmt = "%A, %B %d, %Y %I:%M:%S %p"
        mt = dt(st.st_mtime).strftime(frmt)
        ct = dt(st.st_ctime).strftime(frmt)
        # build command
        return (
            f'$o = Get-Item -LiteralPath "{self.pth_out}"; '
            f'$o.LastWriteTime = "{mt}"; '
            f'$o.CreationTime = "{ct}"'
        )
