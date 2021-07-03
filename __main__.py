"""A collection of scripts that can be easily called from the command line."""


from commandline import openfile
from typing import Callable as C
from winnotify import PlaySound
from subprocess import run
from pathlib import Path
from re import sub
import logging

from argparse import (
    ArgumentParser as ArgParser,
    RawTextHelpFormatter
)
from textwrap import (
    fill,
    dedent
)
from . import src


class main:
    pKwargs = dict(add_help=False,
                   formatter_class=RawTextHelpFormatter)
    hArgs = ['-h', '--help']
    hKwargs = dict(help="show this help message",
                   action='store_true')
    wArgs = ['-w', '--window']
    wKwargs = dict(help="redirect help and errors to a new window",
                   action='store_true')
    console: bool
    dirname: Path
    subs: dict[C, ArgParser]
    parser: ArgParser

    def __init__(self):
        # init vars
        self.dirname = Path(__file__).parent
        self.console = False
        self.subs = dict()
        err = False
        # setup logging
        logfile = self.dirname.joinpath('lib', 'logging.log')
        logging.basicConfig(filename=logfile,
                            filemode='w',
                            level=logging.DEBUG,
                            format='[%(asctime)s] %(levelname)s: %(module)s.%(funcName)s\n%(message)s\n',
                            datefmt='%m/%d/%Y %I:%M:%S%p')
        try:
            self.buildParser()
            self.runScript()
        except Exception:
            logging.exception('')
            err = True
            raise
        finally:
            if logfile.read_text():
                if err:
                    PlaySound()
                if self.console:
                    openfile(logfile, 'min')
                else:
                    print(logfile.read_text())
                    run(['powershell', 'pause'])

    def buildParser(self) -> None:
        # create parser
        self.parser = ArgParser(prog=self.dirname.name,
                                description=__doc__,
                                **self.pKwargs)
        self.parser.add_argument(*self.hArgs, **self.hKwargs)
        self.parser.add_argument(*self.wArgs, **self.wKwargs)
        self.subpars = self.parser.add_subparsers(
            help=f"METHOD DESCRIPTION:\n{'='*20}")
        # create help
        functions = {f: getattr(src, f) for f in src.__all__}
        for name, script in functions.items():
            self.createHelp(name, script)

    def createHelp(self, name: str, script):
        def wrap(txt: str) -> str:
            outstr = str()
            for line in dedent(txt).split('\n'):
                outstr += fill(text=line,
                               width=90)
                outstr += '\n'
            return outstr
        subpar = self.subpars.add_parser(
            name=name,
            description=wrap(script.__doc__),
            help=wrap(script.__doc__),
            **self.pKwargs)
        subpar.add_argument(*self.hArgs, **self.hKwargs)
        subpar.add_argument(*self.wArgs, **self.wKwargs)
        subpar.add_argument('-a', '--args',
                            help=wrap(sub(pattern=r'Parameters.*\n\s*',
                                          repl='',
                                          string=script.__init__.__doc__)),
                            nargs='+')
        subpar.set_defaults(func=script)
        self.subs[script] = subpar

    def runScript(self):
        all_args = self.parser.parse_args()
        self.console = all_args.window
        if all_args.help:
            try:
                logging.info(self.subs[all_args.func].format_help())
            except Exception:
                logging.info(self.parser.format_help())
        else:
            args = all_args.args or list()
            all_args.func(*args)


if __name__ == "__main__":
    main()
