from pathlib import Path as _Path
from re import split as _split

from configparser import (
    ExtendedInterpolation as _ExtInterp,
    ConfigParser as _ConfigParser
)


class _CFG(_ConfigParser):
    def __init__(self):
        _ConfigParser.__init__(self,
                               allow_no_value=False,
                               interpolation=_ExtInterp())
        self.optionxform = str
        self.read_file(open(_Path(__file__).parent.with_name('config.ini')))

    def getlines(self, sct, opt) -> tuple[str, ...]:
        return tuple(self.get(sct, opt)
                     .strip()
                     .split('\n'))


_cfg = _CFG()

# AlterImages
_sct = 'AlterImages'
ALTER_FTYPES = _cfg.getlines(_sct, 'file_types')

# ConvertVideo
_sct = 'ConvertVideo'
CON_WD = max(40, _cfg.getint(_sct, 'console_wd'))
CON_HT = _cfg.getint(_sct, 'console_ht')
CON_SZ_CMD = ('$ps = (Get-Host).ui.rawui; '
              '$sz = $ps.windowsize; '
              f'$sz.width = {CON_WD}; '
              f'$sz.height = {CON_HT}; '
              '$ps.windowsize = $sz; '
              '$bf = $ps.buffersize; '
              f'$bf.width = {CON_WD}; '
              '$ps.buffersize = $bf')
CON_CLOSE_AFTER = _cfg.getint(_sct, 'console_close_after')
CRF_VALS = tuple(
    (int(ht), int(crf)) for ht, crf in
    [_split(r'\s*:\s*', val) for val in
     _cfg.getlines(_sct, 'ffmpeg_crf_values')]
)
CONV_FTYPES = _cfg.getlines(_sct, 'file_types')
CONV_NVENC = _cfg.getboolean(_sct, 'use_hevc_nvenc')
CONV_THREADS = max(1, _cfg.getint(_sct, 'thread_count'))
if CONV_NVENC:
    CONV_THREADS = min(3, CONV_THREADS)
CONV_STREAMS = max(1, _cfg.getint(_sct, 'stream_count'))
CONV_CUTOFF = _cfg.getint(_sct, 'playtime_cutoff')
