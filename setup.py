# -*- coding: utf-8 -*-

from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='pyHMI',
    version='0.0.3',
    description='A set of class for easy build tkinter HMI with Python',
    long_description='',
    author='Loic Lefebvre',
    author_email='loic.celine@free.fr',
    license='MIT',
    url='https://github.com/sourceperl/pyHMI',
    packages=['pyHMI'],
    platforms='any',
    install_requires=required,
)
