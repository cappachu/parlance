
from setuptools import setup, find_packages
import parlance

setup(
    name='parlance',
    version=parlance.__version__,
    description='chat with folks on your local area network',
    author='Codanda B. Appachu',
    url='https://github.com/cappachu/parlance',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'parlance = parlance.parlance:main',
        ]
    },
    install_requires=[
        'urwid',
        'argparse',
    ],
)
