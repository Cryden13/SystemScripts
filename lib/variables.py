from PyQt5.QtGui import QIcon as _QIcon
from re import split as _split
from pathlib import Path

from configparser import (
    ExtendedInterpolation as _ExtInterp,
    ConfigParser as _ConfigParser,
)
from typing import Optional as O, Union as U


class _CFG(_ConfigParser):
    def __init__(self):
        _ConfigParser.__init__(self, allow_no_value=False,
                               interpolation=_ExtInterp())
        self.optionxform = str
        self.read_file(open(Path(__file__).parent.with_name("config.ini")))

    def getlines(self, sct, opt) -> tuple[str, ...]:
        return tuple(self.get(sct, opt).strip().split("\n"))


_cfg = _CFG()

# AlterImages
_sct = "AlterImages"
ALTER_FTYPES = _cfg.getlines(_sct, "file_types")
ALTER_OTYPES = _cfg.getlines(_sct, "output_types") or [".jpg", ".png"]
ALTER_FILL_CLR = _cfg.get(_sct, "fill_color")
