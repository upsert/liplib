import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="liplib",
    version="0.0.3",
    author="upsert",
    author_email="",
    description="Interface module for Lutron Integration Protocol (LIP) over Telnet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/upsert/liplib",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",
        "Intended Audience :: Developers"
    ],
    python_requires='>=3.6',
)
