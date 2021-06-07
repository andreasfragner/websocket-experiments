#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Install usage:
    python setup.py install
    USE_CYTHON=1 python setup.py build_ext --inplace

Release usage:
    python setup.py release --release-type major --repository jetstone-prod
"""

from pathlib import Path

from pkg_resources import parse_requirements
from setuptools import find_namespace_packages, setup

# from setuptools.command.upload import upload

# class UploadCommand(upload):
#     def __init__(self, *args, **kwargs):
#         raise ValueError(
#             "Explicit uploading is not allowed. Use release instead. "
#             "(requires jetstone-common-setuptools)"
#         )


# cmdclass = {"upload": UploadCommand}


# try:
#     from jetstone.common.setuptools.command.release import ReleaseCommand

#     cmdclass["release"] = ReleaseCommand
# except ImportError:
#     pass


def read(filename):
    with open(filename) as fd:
        return fd.read()


def get_requirements(filename):
    if Path(filename).exists():
        return [str(req) for req in parse_requirements(read(filename))]
    return []


extensions = []
entry_points = {}

setup(
    name="wss-runtime",
    version="0.0.0",
    packages=find_namespace_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    entry_points=entry_points,
    ext_modules=extensions,
    author="andreas.fragner",
    author_email="",
    keywords=[""],
    summary="",
    long_description=read("README.md"),
    license=read("LICENSE"),
    url="",
    install_requires=get_requirements("requirements.txt"),
    extras_require={"dev": get_requirements("dev-requirements.txt")},
    classifiers=["Development Status :: 4 - Beta"],
)
