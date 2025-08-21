#!/usr/bin/env python3
"""
Setup script for Industrial Board Alignment Detection System
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="industrial-board-detection",
    version="1.0.0",
    author="Sam Smith",
    author_email="",
    description="Professional computer vision system for detecting misaligned boards in manufacturing",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/sampsmith/industrial-board-detection",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Manufacturing",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "board-detection=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.py"],
    },
    keywords="computer-vision, manufacturing, quality-control, industrial-automation, opencv",
    project_urls={
        "Bug Reports": "https://github.com/sampsmith/industrial-board-detection/issues",
        "Source": "https://github.com/sampsmith/industrial-board-detection",
        "Documentation": "https://github.com/sampsmith/industrial-board-detection#readme",
    },
)
