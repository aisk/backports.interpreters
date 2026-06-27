from setuptools import setup, find_namespace_packages


setup(
    name="backports.interpreters",
    description="Backport of the concurrent.interpreters module described in PEP 734",
    author="An Long",
    url="https://github.com/aisk/backports.interpreters",
    version="0.3.1",
    license="PSF-2.0",
    packages=find_namespace_packages(include=["backports.*"]),
    python_requires=">=3.8",
    classifiers=[
        "License :: OSI Approved :: Python Software Foundation License",
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
