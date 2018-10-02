# -*- coding: utf-8 -*-
import shelve
import subprocess
from concurrent.futures import ThreadPoolExecutor
from difflib import ndiff
from termcolor import colored
from terminaltables import SingleTable

try:
    from pathlib import Path

    Path().expanduser()
except (ImportError, AttributeError):
    from pathlib2 import Path  # Patch for Python 2.x

from requests_futures.sessions import FuturesSession
from requests.auth import HTTPBasicAuth

DATA_DIR = Path.home().joinpath(".udebugcli")
if not DATA_DIR.exists():
    DATA_DIR.mkdir()

SHELVE_PATH = str(DATA_DIR.joinpath('config'))


def set_login(username, password):
    with shelve.open(SHELVE_PATH) as db:
        db['username'] = username
        db['password'] = password
        db.sync()


def get_login():
    with shelve.open(SHELVE_PATH) as db:
        if "username" not in db or "password" not in db:
            raise Exception("Must set username and password first.")

        return db['username'], db['password']


def get_(session, url, params=None, background_callback=None):
    username, password = get_login()
    auth = HTTPBasicAuth(username, password)

    return session.get(url, auth=auth, params=params, background_callback=background_callback)


def retrieve_output(input_id, session):
    def callback(session, response):
        response.data = response.json()[0]

    return get_(session, 'https://www.udebug.com/output_api/output/retrieve.json',
                params={"input_id": input_id},
                background_callback=callback)


def retrieve_input(input_id, session):
    def callback(session, response):
        response.data = response.json()[0]

    return get_(session, 'https://www.udebug.com/input_api/input/retrieve.json',
                params={"input_id": input_id},
                background_callback=callback)


class TestCase(object):
    def __init__(self, session, test_case_dict):
        self.id = test_case_dict['id']
        self.user = test_case_dict['user']
        self.date = test_case_dict['Date']
        self.votes = test_case_dict['Votes']

        self._input = test_case_dict.get("input", None)
        if not self._input:
            self._retrieve_input_request = retrieve_input(self.id, session)

        self._output = test_case_dict.get("output", None)
        if not self._output:
            self._retrieve_output_request = retrieve_output(self.id, session)

    @property
    def input(self):
        if not self._input:
            self._input = self._retrieve_input_request.result().data
            self._retrieve_input_request = None
        return self._input

    @property
    def output(self):
        if not self._output:
            self._output = self._retrieve_output_request.result().data
            self._retrieve_output_request = None
        return self._output

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user,
            "Date": self.date,
            "Votes": self.votes,
            "input": self.input,
            "output": self.output
        }


class TestCaseException(Exception):
    def __init__(self, test_case, got_output):
        self.test_case = test_case
        self.got_output = got_output

    def report(self):
        print(colored("FAILED!", "red"), "Got wrong output...")

        table_data = [[self.test_case.input.rstrip("\n\r")]]
        table_instance = SingleTable(table_data, 'Input')
        table_instance.inner_heading_row_border = False
        table_instance.inner_row_border = False
        table_instance.inner_column_border = False

        print(table_instance.table)

        diff = ndiff(self.test_case.output.splitlines(1), self.got_output.splitlines(1))

        table_data = []
        for line in diff:
            line = line.rstrip("\n\r")
            if line.startswith("+"):
                table_data.append([colored("GOT", "red"), colored(line, "red")])
            elif line.startswith("-"):
                table_data.append([colored("EXPECTED", "green"), colored(line, "green")])
            elif line.startswith("?"):
                table_data.append(["", colored(line, "yellow")])
            else:
                table_data.append(["", line])

        table_instance = SingleTable(table_data, 'Output Diff')
        table_instance.inner_heading_row_border = False
        table_instance.inner_row_border = False
        table_instance.inner_column_border = False

        print(table_instance.table)


def _retrieve_test_cases(judge_alias, problem_id):
    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=1))
    r = get_(session, 'https://www.udebug.com/input_api/input_list/retrieve.json',
             params={"judge_alias": judge_alias, "problem_id": problem_id})

    input_list = r.result().json()
    print("Retrieving input and output for {} test cases...".format(len(input_list)))

    data = [TestCase(session, test_case_dict) for test_case_dict in input_list]
    return data


def retrieve_test_cases(judge_alias, problem_id):
    shelve_path = str(DATA_DIR.joinpath('{}-{}'.format(judge_alias, problem_id)))
    with shelve.open(shelve_path) as db:
        data = db.get("data", None)
        if not data:
            data = _retrieve_test_cases(judge_alias, problem_id)

            db["data"] = [d.to_dict() for d in data]
            db.sync()
        else:
            data = [TestCase(None, d) for d in data]

        return data


def run_test_case(cmd, test_case):
    input = test_case.input

    p = subprocess.run(cmd, stdout=subprocess.PIPE, input=input.encode('utf8'))
    got_output = p.stdout.decode('utf8')

    expected_output = test_case.output

    if got_output != expected_output:
        raise TestCaseException(test_case, got_output)


def run(judge_alias, problem_id, cmd, failfast=False):
    test_cases = retrieve_test_cases(judge_alias, problem_id)
    for test_case in test_cases:
        try:
            run_test_case(cmd, test_case)
        except TestCaseException as e:
            e.report()
            if failfast:
                return
