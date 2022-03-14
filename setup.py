""" Setuptools install script """
from setuptools import setup

setup(
    name="py_sw2abc",
    version="0.1",
    py_modules=["sw2abc"],
    install_requires=["Click"],
    entry_points={"console_scripts": ["py_sw2abc=sw2abc:main"]},
)
