#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Copyright (C) 2015 Faurecia (China) Holding Co.,Ltd.

All rights reserved.
Name: setup.py
Author: Canux CHENG canuxcheng@gmail.com
Version: V1.0.0.0
Time: Fri 05 Aug 2016 09:59:29 AM CST

Description:
"""
import os

from setuptools import setup, find_packages

import plugin


def read(readme):
    """Give reST format README for pypi."""
    extend = os.path.splitext(readme)[1]
    if (extend == '.rst'):
        import codecs
        return codecs.open(readme, 'r', 'utf-8').read()
    elif (extend == '.md'):
        import pypandoc
        import codecs
        return codecs.open(pypandoc.convert(readme, 'rst'), 'r', 'utf-8').read()

INSTALL_REQUIRES = [
    'pymysql',
    'pymssql',
    'paramiko',
    'pysnmp',
    'pyvmomi',
    'sh'
]

setup(
    name='xplugin',
    version=plugin.__VERSION__,
    author='Canux CHENG',
    author_email='canuxcheng@gmail.com',
    maintainer='Canux CHENG',
    maintainer_email='canuxcheng@gmail.com',
    description='Common interface for tons of protocal, used for monitoring tools, like nagios/icinga...',
    long_description=read('README.rst'),
    license='GPL',
    platforms='any',
    keywords='monitoring nagios plugin',
    url='https://github.com/crazy-canux/xplugin',
    install_requires=INSTALL_REQUIRES,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Plugins",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Topic :: System :: Monitoring"
    ],
)
