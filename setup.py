#!/usr/bin/env python3
"""
Setup script for ZenFolio - A minimal, powerful academic website generator
"""

from setuptools import setup, find_packages

setup(
    name="zenfolio",
    version="0.1.0",
    description="A Zen approach to academic websites",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Jean Kossaifi",
    url="https://github.com/JeanKossaifi/zenfolio",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "zencfg>=0.1.0",
        "markdown>=3.4.0",
        "jinja2>=3.1.0",
        "bibtexparser>=1.4.0",
        "python-frontmatter>=1.0.0",
        "nbformat>=5.0.0",
        "nbconvert>=6.5.0",
    ],
    extras_require={
        "dev": ["pytest", "ipykernel", "notebook"],
    },
    entry_points={
        "console_scripts": [
            "zenfolio=zenfolio.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Software Development :: Documentation",
    ],
    keywords=["academic", "website", "static-site-generator", "zencfg"],
) 