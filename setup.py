#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script"""

from setuptools import setup

setup(
    name='idlerpgslack',
    version='0.1',
    description='An IdleRPG bot that uses the Slack API',
    url='https://github.com/mohebifar/idlerpg-slack',
    author='Mark Stacey',
    author_email='markjstacey@gmail.com',
    license='MIT',
    packages=['idlerpgslack'],
    install_requires=[
        'slackclient'
    ],
    python_requires='>=2.7',
    entry_points={
        'console_scripts': [
            'idlerpgslack=idlerpgslack.cli:main'
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat',
        'Topic :: Games/Entertainment :: Role-Playing'
    ],
    keywords='slack idlerpg rpg bot',
    zip_safe=False 
)