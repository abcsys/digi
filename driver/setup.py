from setuptools import setup, find_packages

setup(
    name="digi",
    version="0.2.8",
    description="Digi driver library",
    author="Team Digi",
    author_email="silveryfu@gmail.com",
    license="BSD-3-Clause License",
    packages=find_packages(exclude=("tests",)),
    python_requires='>=3.7',
    include_package_data=True,
    install_requires = open('requirements.txt').readlines(),
)
