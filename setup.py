# setup.py
from setuptools import setup, find_packages

setup(
    name="factorymanager",
    version="0.1.0",
    description="A manager for programmatically controlling linuxserver.io style Docker containers with robotgo-cli",
    author="Sam Pagon",
    author_email="sp3692@drexel.edu",
    packages=find_packages(),  
    install_requires=[
        "docker", 
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
