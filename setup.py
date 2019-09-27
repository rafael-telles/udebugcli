# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""

import re
from setuptools import setup

version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('udebugcli/udebugcli.py').read(),
    re.M
).group(1)

with open("README.md", "rb") as f:
    long_descr = f.read().decode("utf-8")

setup(
    name="udebugcli",
    packages=["udebugcli"],
    entry_points={
        "console_scripts": ['udebug = udebugcli.udebugcli:main']
    },
    version=version,
    description="Utility CLI for automatically testing solutions of competitive programming online judges.",
    long_description=long_descr,
    author="Rafael Telles",
    author_email="rafael@telles.pw",
    install_requires=[
        "docopt==0.6.2",
        "PyInquirer==1.0.2",
        "requests==2.20.0",
        "requests-futures==0.9.7",
        "terminaltables==3.1.0",
        "termcolor==1.1.0"
    ],
    url="https://github.com/rafael-telles/udebugcli",
)
