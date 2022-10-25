from setuptools import setup, find_packages

URLS = {
}

setup(
    name="digi",
    version="0.2.5",
    description="Digi driver library",
    url=URLS,
    author="Team Digi",
    author_email="silveryfu@gmail.com",
    license="BSD-3-Clause License",
    packages=find_packages(exclude=("tests",)),
    python_requires='>=3.7',
    include_package_data=True,
    install_requires=[
        "pyyaml",
        "inflection",
        "python-box",
        "kubernetes",
        'kopf',
        "zed",
        "dash",
        "pandas",
    ],
)
