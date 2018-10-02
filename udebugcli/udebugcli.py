#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""uDebug Command Line Interface

Usage:
  udebug login
  udebug retrieve <judge_alias> <problem_id>
  udebug run <judge_alias> <problem_id> <cmd> [--failfast]

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


def cmd_retrieve(arguments):
    lib.retrieve_test_cases(arguments['<judge_alias>'], arguments['<problem_id>'])


def cmd_run(arguments):
    lib.run(arguments['<judge_alias>'], arguments['<problem_id>'], arguments["<cmd>"], arguments["--failfast"])


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
        elif arguments["retrieve"]:
            cmd_retrieve(arguments)
        elif arguments["run"]:
            cmd_run(arguments)
        else:
            cmd_help()
    except Exception as e:
        print(e)
        exit(1)


if __name__ == "__main__":
    main()
