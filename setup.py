from setuptools import setup, find_packages

setup(
    name="util",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pyexiftool",
        "python-dateutil",
        "pytz",
        "tzlocal",
    ],
    entry_points={
        "console_scripts": [
            "exif2mtime=scripts.exif2mtime:main",
            # Add other entry points here if needed
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
