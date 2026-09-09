from setuptools import setup, find_packages

setup(
    name="vcm-ml",
    version="1.0.0",
    description="VCM - Model DNA Version Control Platform",
    author="VCM Team",
    packages=find_packages(include=["vcm", "vcm.*"]),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "pyyaml>=6.0.0",
        "tabulate>=0.9.0",
        "GitPython>=3.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "vcm=vcm.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
)
