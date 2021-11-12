from setuptools import setup, find_packages

URLS = {
    # TBD
}

setup(
    name="digi",
    version="0.1.6",
    description="dSpace driver library",
    url=URLS,
    author="Silvery Fu",
    author_email="silveryfu@gmail.com",
    license="Apache 2.0",
    packages=find_packages(exclude=("tests",)),
    python_requires='>=3.7',
    include_package_data=True,
    install_requires=[
        "kubernetes",
        'kopf',
        "pyyaml",
        "pyjq",
        "inflection",
        "python-box",
    ],
)
