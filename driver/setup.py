from setuptools import setup, find_packages

URLS = {
}

setup(
    name="digi",
    version="0.2.0",
    description="dSpace driver library",
    url=URLS,
    author="Silvery Fu",
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
