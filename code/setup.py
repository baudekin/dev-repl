# -*- coding: utf-8 -*-

__author__ = "mkambol"

from setuptools import setup, find_packages

setup(
    name='devrepl',
    version='1.0',
    description='',
    author='mkambol',
    install_requires=['datetime', 'PyInquirer', 'colorama', 'gitpython', 'tqdm', 'jira', 'terminaltables', 'python-dateutil'],
    license=license,
    packages=find_packages(include=['*'])
    )
