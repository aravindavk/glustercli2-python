import os
import re
from setuptools import setup

VERSION = "0.3.0"

with open("docs/README.adoc", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='glustercli2',
    version=VERSION,
    description='Python bindings for GlusterFS CLI',
    long_description=long_description,
    long_description_content_type="text/plain",
    license='Apache-2.0',
    author='Aravinda Vishwanathapura',
    author_email='mail@aravindavk.in',
    url='https://github.com/aravindavk/glustercli2-python',
    packages=["glustercli2"],
    install_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Filesystems',
    ],
)
