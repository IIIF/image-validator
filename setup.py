from setuptools import setup
import os
from pathlib import Path

this_directory = Path(__file__).parent
if os.path.exists("version.txt"):
    VERSION = (this_directory / "version.txt").read_text().strip()
else:
    VERSION = "0.0.0.dev0"    

REQUIREMENTS = [
    "bottle>=0.12.1",
    "python-magic>=0.4.12",
    "lxml>=3.7.0",
    "Pillow>=6.2.2"
]

# Read dev requirements from requirements.txt
with open("requirements.txt") as f:
    DEV_REQUIREMENTS = f.read().splitlines()

setup(
    name='iiif-validator',
    version=VERSION,
    packages=['iiif_validator', 'iiif_validator.tests'],
    scripts=['iiif-validator.py', 'iiif-validate.py'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Environment :: Web Environment"
    ],
    python_requires='>=3',
    author='IIIF Contributors',
    author_email='simeon.warner@cornell.edu',
    description='IIIF Image API Validator',
    long_description=open('README').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/IIIF/image-validator',
    install_requires=REQUIREMENTS,
    extras_require={
        "dev": DEV_REQUIREMENTS
    })
