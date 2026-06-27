from setuptools import setup, find_namespace_packages


setup(
    name="backports.interpreters",
    description="Backport of the concurrent.interpreters module described in PEP 734",
    author="AN Long",
    url="https://github.com/aisk/backports.interpreters",
    version="0.3.0",
    packages=find_namespace_packages(include=["backports.*"]),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    extras_require={"dev": ["pytest"]},
)
