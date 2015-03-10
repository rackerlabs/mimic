"""
Setup file for mimic
"""

from setuptools import setup, find_packages

setup(
    name='mimic',
    version='1.3.0',
    description='An API-compatible mock service',
    packages=find_packages(exclude=[]) + ["twisted.plugins"],
    package_dir={'mimic': 'mimic'},
    install_requires=[
        "characteristic>=14.2.0",
        "klein>=0.2.1",
        "twisted>=14.0.2",
        "jsonschema>=2.0",
        "treq>=0.2.1",
        "six>=1.6.0",
    ],
    include_package_data=True,
    license="Apache License, Version 2.0"
)
