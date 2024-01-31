from setuptools import setup


setup(
    name="backports.interpreters",
    description='Backport of Python interpreters module described in PEP554',
    author="AN Long",
    url="https://github.com/aisk/backports.interpreters",
    version="0.2.1",
    py_modules=["backports.interpreters"],
    namespace_packages=["backports"],
    python_requires=">=3.8",
    extras_require={"dev": ["pytest"]}
)
