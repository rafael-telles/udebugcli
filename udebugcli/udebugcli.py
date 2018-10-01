#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""uDebug Command Line Interface

Usage:
  udebug login
  udebug test <judge_alias> <problem_id> <cmd>

"""

from docopt import docopt
from PyInquirer import prompt


from . import lib


__version__ = "0.0.1"


def cmd_help():
    print(__doc__)


def cmd_login():
    questions = [
        {
            'type': 'input',
            'name': 'username',
            'message': 'Username',
        }, {
            'type': 'password',
            'name': 'password',
            'message': 'Password',
        }
    ]
    answers = prompt(questions)

    lib.set_login(answers["username"], answers["password"])


def cmd_test(arguments):
    lib.test(arguments['<judge_alias>'], arguments['<problem_id>'])


def main():
    try:
        arguments = docopt(__doc__, help=False, version=__version__)
    except SystemExit:
        cmd_help()
        exit(1)
        return

    try:
        if arguments["login"]:
            cmd_login()
        elif arguments["test"]:
            cmd_test(arguments)
        else:
            cmd_help()
    except Exception as e:
        print(e)
        exit(1)


if __name__ == "__main__":
    main()
