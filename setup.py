#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'pandas>=0.18.1',
    'lxml>=3.6.4',
    'future>=0.15.2'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pandasplexos',
    version='0.1.0',
    description="Pandas Plexos wrapper",
    long_description=readme + '\n\n' + history,
    author="Dheepak Krishnamurthy",
    author_email='kdheepak89@gmail.com',
    url='https://github.com/kdheepak/pandasplexos',
    packages=[
        'pandasplexos',
    ],
    package_dir={'pandasplexos':
                 'pandasplexos'},
    entry_points={
        'console_scripts': [
            'pandasplexos=pandasplexos.cli:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='pandasplexos',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
