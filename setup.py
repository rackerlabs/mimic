"""
Setup file for mimic
"""

from setuptools import setup, find_packages

setup(
    name='mimic',
    version='0.0.0',
    description='An API-compatible mock service',
    packages=find_packages(exclude=[]),
    package_data={'': ['LICENSE']},
    package_dir={'mimic': 'mimic'},
    install_requires=[
        "characteristic==0.1.0",
        "klein==0.2.1",
        "twisted>=13.2.0",
        "jsonschema==2.0",
        "treq",
        "six",
    ],
    include_package_data=True,
    license=open('LICENSE').read()
)
