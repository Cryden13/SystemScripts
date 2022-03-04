from concurrent.futures import ThreadPoolExecutor
from subprocess import run
from pathlib import Path
from re import match

from winnotify import (
    InputDialog as InDlg,
    Messagebox as Mbox
)

from ..lib.variables import (
    ALTER_FTYPES,
    ALTER_OTYPES,
    ALTER_FILL_CLR
)


class AlterImages:
    """Convert, resize, and/or fill image files with specified extensions (from config.ini) within this folder to 2k and optionally convert them to jpg.

    3rd-party Requirements
    ----------
    ImageMagick (https://imagemagick.org/)
    """

    def __init__(self, workingdir: str):
        """\
        Parameters
        ----------
        workingdir (str): The path of the directory that contains the images
        """

        # init vars
        self.dirname = Path(workingdir).resolve()
        sizes = {'None': '',
                 '1280x720': 'SD',
                 '1920x1080': 'HD',
                 '2560x1440': '2K'}
        # get preferences
        wgt_cnv = InDlg.ChWgt.combobox(options=['None', *ALTER_OTYPES],
                                       default=ALTER_OTYPES[0])
        wgt_rsz = InDlg.ChWgt.combobox(options=sizes.keys(),
                                       default='2560x1440')
        wgt_usz = InDlg.ChWgt.textbox(hint='Optional override. WxH')
        wgt_fbg = InDlg.ChWgt.combobox(options=sizes.keys(),
                                       default='2560x1440')
        wgt_usf = InDlg.ChWgt.textbox(hint='Optional override. WxH')
        wgt_tbs = InDlg.ChWgt.checkbox(default=True)
        wgt_rec = InDlg.ChWgt.checkbox()
        ans = InDlg.multiinput(title="Alter Images",
                               message=f"Altering image files in\n<{self.dirname}>",
                               input_fields=[
                                   ('Convert to', wgt_cnv),
                                   ('Resize', wgt_rsz),
                                   ('User resize', wgt_usz),
                                   ('Fill background', wgt_fbg),
                                   ('User fill size', wgt_usf),
                                   ('Trim blackspace', wgt_tbs),
                                   ('Recurse folders', wgt_rec)
                               ])
        if not ans:
            return
        # get vars
        self.resstr = ''
        if ans['Convert to'] == 'None':
            convert = ''
        else:
            convert = ans['Convert to']
            self.resstr = '(Conv)'

        if ans['Trim blackspace']:
            tbs = '-fuzz 5% -trim'
            self.resstr = '(Trim)'
        else:
            tbs = ''

        if ans['User fill size']:
            fbg = (f"-background {ALTER_FILL_CLR} "
                   f"-gravity center -extent {ans['User fill size']}")
            self.resstr = '(Fill)'
        elif ans['Fill background'] == 'None':
            fbg = ''
        else:
            fbg = (f"-background {ALTER_FILL_CLR} "
                   f"-gravity center -extent {ans['Fill background']}")
            self.resstr = '(Fill)'

        if ans['User resize']:
            rsz = f"-resize {ans['User resize']}"
            self.resstr = f"({ans['User resize']})"
        elif ans['Resize'] == 'None':
            rsz = ''
        else:
            rsz = f"-resize {ans['Resize']}"
            self.resstr = f"({sizes.get(ans['Resize'])})"

        self.check(self.resstr)
        self.alter = f"{tbs} {rsz} {fbg}"
        recurse = ans['Recurse folders']
        # find files
        func = self.dirname.rglob if recurse else self.dirname.glob
        regex = f'\(({"|".join([i for i in sizes.values() if i])})\)'
        files = [f'"{f.relative_to(self.dirname)}"' for f in func('*.*')
                 if f.suffix in ALTER_FTYPES
                 and not match(regex, f.name)]
        self.check(files)
        files = [files[i:i + 5] for i in range(0, len(files), 5)]
        # run threads
        self.fname, self.ext = ('t', convert) if convert else ('f', '')
        self.err = list()
        with ThreadPoolExecutor(max_workers=5) as ex:
            ex.map(self.processing, files)
        # show results
        self.err = '\n\n'.join(self.err)
        err = f'Error:  \n{self.err}' if self.err else ''
        Mbox.showinfo(title="AlterImages Result",
                      message=("Image processing completed!\t\n"
                               f"{err}"))

    def processing(self, files: list[str]):
        cmd = (f'magick {" ".join(files)} {self.alter} '
               f'-set filename:f "%{self.fname}" '
               f'+adjoin "{self.resstr} %[filename:f]{self.ext}"')
        err = run(cmd, cwd=self.dirname, capture_output=True, text=True).stderr
        if err:
            self.err.append(err)
        return

    @ staticmethod
    def check(this):
        if this:
            return
        else:
            Mbox.showerror(title="AlterImages Error",
                           message="There's nothing to do!")
            raise SystemExit
