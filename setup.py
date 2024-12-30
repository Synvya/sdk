from setuptools import setup, find_packages

setup(
    name="agentstr",
    version="0.0.1",
    author="Alejandro Gil",
    description="A library for collaborative AI agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/synvya/agentstr",
    packages=find_packages(),
    install_requires=[
        # List your dependencies here
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
