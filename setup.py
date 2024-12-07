from setuptools import setup, find_packages

setup(
    name="colliderml",
    version="0.1.0",
    description="A modern machine learning library for high-energy physics data analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Daniel Murnane",
    author_email="dtmurnane@lbl.gov",
    url="https://github.com/murnanedaniel/colliderml",
    packages=find_packages(),
    python_requires=">=3.10,<3.12",
    install_requires=[
        "requests>=2.31.0",
        "tqdm>=4.66.0",
        "numpy>=1.24.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "ruff>=0.1.6",
            "mypy>=1.7.0",
            "mkdocs-material>=9.4.0",
            "mkdocstrings[python]>=0.24.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    project_urls={
        "Documentation": "https://murnanedaniel.github.io/colliderml",
        "Source": "https://github.com/murnanedaniel/colliderml",
        "Issues": "https://github.com/murnanedaniel/colliderml/issues",
    },
) 