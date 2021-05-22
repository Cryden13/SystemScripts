"""A collection of scripts that can be easily called from the command line."""


from argparse import (RawTextHelpFormatter as HelpFrmt,
                      ArgumentParser as ArgParser)
from contextlib import redirect_stdout
from typing import (Callable as C,
                    Union as U)
from traceback import format_exc
from textwrap import dedent
from pathlib import Path
from io import StringIO

from ._msg import _show_info
from . import *


class _run:
    pKwargs = dict(add_help=False,
                   formatter_class=HelpFrmt)
    hArgs = ['-h', '--help']
    hKwargs = dict(help="show this help message",
                   action='store_true')
    wArgs = ['-w', '--window']
    wKwargs = dict(help="redirect help and errors to a new window",
                   action='store_true')
    dirname: Path
    parser: ArgParser
    subs: dict[C, dict[str, U[str, ArgParser]]]

    def __init__(self):
        self.dirname = Path(__file__).parent
        self.buildParser()
        self.subs = dict()
        funcNames = [f.stem for f in self.dirname.glob('[!_]*.py')]
        for name, script in globals().items():
            if name in funcNames:
                self.createHelp(name, script)
        self.getArgs()

    def buildParser(self) -> None:
        self.parser = ArgParser(
            prog=self.dirname.name,
            description=__doc__,
            **self.pKwargs)
        self.parser.add_argument(*self.hArgs, **self.hKwargs)
        self.parser.add_argument(*self.wArgs, **self.wKwargs)
        self.subpars = self.parser.add_subparsers(
            help="Method description:")

    def createHelp(self, name: str, script):
        subpar = self.subpars.add_parser(name=name,
                                         description=script.__doc__,
                                         help=script.__doc__,
                                         **self.pKwargs)
        subpar.add_argument(*self.hArgs, **self.hKwargs)
        subpar.add_argument(*self.wArgs, **self.wKwargs)
        subpar.add_argument('-a', '--args',
                            help=dedent(script.main.__doc__),
                            nargs='+')
        subpar.set_defaults(func=script.main)
        self.subs[script.main] = {'name': name, 'sparser': subpar}

    def getArgs(self):
        sIO = StringIO()
        with redirect_stdout(sIO):
            all_args = self.parser.parse_args()
            if all_args.help:
                try:
                    self.subs[all_args.func]['sparser'].print_help()
                except Exception:
                    self.parser.print_help()
        out = sIO.getvalue()
        try:
            fname = self.subs[all_args.func]['name']
        except Exception:
            fname = "Main"
        if out:
            _show_info(all_args.window, "help", fname, out)
            raise SystemExit
        else:
            try:
                args = all_args.args or list()
                all_args.func(*args)
            except:
                _show_info(all_args.window, "error", fname, format_exc())


if __name__ == "__main__":
    _run()
