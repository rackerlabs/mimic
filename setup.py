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
    include_package_data=True,
    license=open('LICENSE').read()
)
