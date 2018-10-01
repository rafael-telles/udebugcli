# -*- coding: utf-8 -*-
import shelve
from concurrent.futures import ThreadPoolExecutor

try:
    from pathlib import Path

    Path().expanduser()
except (ImportError, AttributeError):
    from pathlib2 import Path  # Patch for Python 2.x

import requests
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


def get_(session, url, params=None):
    username, password = get_login()
    auth = HTTPBasicAuth(username, password)

    return session.get(url, auth=auth, params=params)


def retrieve_output(input_id, session):
    return get_(session, 'https://www.udebug.com/output_api/output/retrieve.json',
                params={"input_id": input_id})


def retrieve_input(input_id, session):
    return get_(session, 'https://www.udebug.com/input_api/input/retrieve.json',
                params={"input_id": input_id})


def test(judge_alias, problem_id):
    session = FuturesSession(executor=ThreadPoolExecutor(max_workers=1))
    r = get_(session, 'https://www.udebug.com/input_api/input_list/retrieve.json',
             params={"judge_alias": judge_alias, "problem_id": problem_id})

    input_list = r.result().json()

    for input in input_list:
        input_id = input['id']
        input['data'] = retrieve_input(input_id, session)
        input['expected_output'] = retrieve_output(input_id, session)
    for input in input_list:
        input['data'] = input['data'].result().json()
        input['expected_output'] = input['expected_output'].result().json()
    for input in input_list:
        print(input)
