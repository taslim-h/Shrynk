from setuptools import find_packages, setup


setup(
    name="shrynk",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "shrynk=shrynk.cli:main",
        ],
    },
    install_requires=["PyQt5"],
)
