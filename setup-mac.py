"""
Setup file for mimic
"""

from setuptools import setup, find_packages

setup(
    name='mimic',
    version='1.3.0',
    description='An API-compatible mock service',
    app=['start-app.py'],
    options={
        'py2app': {
            'includes': ['syslog', 'mimic.test.*'],
            'data-files': ['gui/mimic.nib']
            'argv_emulation': True
        }
    }
)
