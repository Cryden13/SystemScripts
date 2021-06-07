from pathlib import Path

from configparser import (
    ExtendedInterpolation as ExtInterp,
    ConfigParser
)


cfgfile = Path(__file__).parent.with_name('config.ini')
cfg = ConfigParser(allow_no_value=False,
                   interpolation=ExtInterp())
cfg.optionxform = str
cfg.read_file(open(cfgfile))

CRF_VALUES = tuple(
    (int(ht), int(crf)) for ht, crf in
    [
        val.split(':') for val in
        (
            cfg.get('DEFAULT', 'ffmpeg_crf_values')
            .strip()
            .split('\n')
        )
    ]
)

ALTER_FTYPES = tuple(cfg.get('AlterImages', 'file_types')
                     .strip()
                     .split('\n'))

COMP_FTYPES = tuple(cfg.get('CompressVideo', 'file_types')
                    .strip()
                    .split('\n'))

CONV_FTYPES = tuple(cfg.get('ConvertVideo', 'file_types')
                    .strip()
                    .split('\n'))
CONV_TO = cfg.get('ConvertVideo', 'convert_to').strip()
CONV_CODEC = cfg.get('ConvertVideo', 'ffmpeg_codec').strip()
