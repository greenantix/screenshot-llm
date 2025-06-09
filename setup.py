#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="screenshot-llm",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "pillow",
        "pystray",
        "pygments",
        "openai>=1.0.0",
        "anthropic>=0.3.0",
        "python-xlib",
    ],
    entry_points={
        "console_scripts": [
            "screenshot-llm=screenshot_llm.main:main",
        ],
    },
    python_requires=">=3.8",
    author="ScreenshotLLM Team",
    description="Screenshot-based LLM Assistant",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: Desktop Environment :: Desktop Automation",
    ],
)