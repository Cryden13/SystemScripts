from PyQt5.QtGui import QIcon as _QIcon
from re import split as _split
from pathlib import Path

from configparser import (
    ExtendedInterpolation as _ExtInterp,
    ConfigParser as _ConfigParser
)
from typing import (
    Optional as O,
    Union as U
)


class _CFG(_ConfigParser):
    def __init__(self):
        _ConfigParser.__init__(self,
                               allow_no_value=False,
                               interpolation=_ExtInterp())
        self.optionxform = str
        self.read_file(open(Path(__file__).parent.with_name('config.ini')))

    def getlines(self, sct, opt) -> tuple[str, ...]:
        return tuple(self.get(sct, opt)
                     .strip()
                     .split('\n'))


_cfg = _CFG()

# AlterImages
_sct = 'AlterImages'
ALTER_FTYPES = _cfg.getlines(_sct, 'file_types')
ALTER_OTYPES = _cfg.getlines(_sct, 'output_types') or ['.jpg', '.png']
ALTER_FILL_CLR = _cfg.get(_sct, 'fill_color')


# ConvertVideo
_sct = 'ConvertVideo'
CONV_ICON = _QIcon(str(Path(__file__).with_name('conv_icon.ico')))
CONV_FTYPES = _cfg.getlines(_sct, 'file_types')
CONV_NVENC = _cfg.getboolean(_sct, 'use_hevc_nvenc')
CONV_CON_WD = max(60, _cfg.getint(_sct, 'console_wd')) - 1
CONV_CON_HT = _cfg.getint(_sct, 'console_ht')
CONV_CON_SZ_CMD = ('$ps = (Get-Host).ui.rawui; '
                   '$sz = $ps.windowsize; '
                   f'$sz.width = {CONV_CON_WD}; '
                   f'$sz.height = {CONV_CON_HT}; '
                   '$ps.windowsize = $sz; '
                   '$bf = $ps.buffersize; '
                   f'$bf.width = {CONV_CON_WD}; '
                   '$ps.buffersize = $bf')
CONV_CON_CLOSE_AFTER = _cfg.getint(_sct, 'console_close_after')
CONV_CRF_VALS = tuple(
    (int(ht), int(crf)) for ht, crf in
    [_split(r'\s*:\s*', val) for val in
     _cfg.getlines(_sct, 'ffmpeg_crf_values')]
)
CONV_AUD_LANGS = {x[0]: x[1] for x in
                  [line.split(':') for line in _cfg.getlines(_sct, 'aud_stream_langs')]}
CONV_SUB_LANGS = {x[0]: x[1] for x in
                  [line.split(':') for line in _cfg.getlines(_sct, 'sub_stream_langs')]}
CONV_STREAMS = max(0, _cfg.getint(_sct, 'stream_count'))
CONV_OVERWRITE = _cfg.getboolean(_sct, 'overwrite_original')
CONV_DO_SCALE = _cfg.getboolean(_sct, 'scale_video')
CONV_DO_CROP = _cfg.getboolean(_sct, 'crop_blackspace')
CONV_KEEP_FAIL = _cfg.getboolean(_sct, 'keep_failures')
CONV_KEEP_ERROR = _cfg.getboolean(_sct, 'keep_errors')
CONV_RECURSE = _cfg.getboolean(_sct, 'recurse_folders')
CONV_CUTOFF = _cfg.getint(_sct, 'playtime_cutoff')
CONV_THREADS = max(1, _cfg.getint(_sct, 'thread_count'))
if CONV_NVENC:
    CONV_THREADS = min(3, CONV_THREADS)
