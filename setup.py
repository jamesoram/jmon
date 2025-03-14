from setuptools import setup, find_packages

setup(
    name="jmon",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pytest',
        'pytest-asyncio'
    ],
    entry_points={
        'console_scripts': [
            'jmon=jmon.main:main',
        ],
    },
)
