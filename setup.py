import os
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="dirsearch-mcp",
    version="1.0.0",
    author="DirsearchMCP Team",
    author_email="contact@dirsearch-mcp.com",
    description="Intelligent directory scanner with AI-powered MCP coordination",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/dirsearch-mcp/dirsearch-mcp",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "dirsearch-mcp=cli.interactive_menu:main",
            "dscan=cli.interactive_menu:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "wordlists/general/*.txt",
            "wordlists/platform/*.txt", 
            "wordlists/specialized/*.txt",
            "config.json",
        ],
    },
    zip_safe=False,
)